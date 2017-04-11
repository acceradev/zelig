import asyncio
import contextlib
import functools
import logging
import signal

import aiohttp
from aiohttp import web

import vcr
from vcr.errors import UnhandledHTTPRequestError

from config import config_app
from constants import ZeligMode, RecordMode
from report import Reporter
from matchers import match_responses
from utils import (
    extract_response_info, extract_request_info, extract_vcr_request_info, get_response_from_cassette, wait,
    load_cassette
)


logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)


async def simulate_client(app, loop, report):
    logger.info('Loading cassette {cassette}'.format(cassette=app['ZELIG_CASSETTE_FILE']))
    requests, responses = load_cassette(app['ZELIG_CASSETTE_FILE'])
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    offset = requests[0].timestamp
    for (request, original_response) in zip(requests, responses):
        await wait(request.timestamp - offset, original_response['latency'], loop=loop)
        request_info = extract_vcr_request_info(request)
        # TODO: handle errors that may occur
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.request(**request_info) as response:
                received_response = await extract_response_info(response)
                match = match_responses(original_response, received_response, app['RESPONSE_MATCH_ON'])
                report.append({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': 'Responses {}'.format('match' if match else 'mismatch')
                })


async def observe(request, cassette, report):
    request_info = await extract_request_info(request)
    original_response = get_response_from_cassette(cassette, request_info)
    received_response = None
    request_matched = (original_response is not None)
    write_to_log = not request_matched

    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            if request_matched:
                # Match responses only when request matched
                received_response = await extract_response_info(response)
                match = match_responses(original_response, received_response, request.app['RESPONSE_MATCH_ON'])
                logger.debug('Request to {url}. Responses match: {match}'.format(url=request_info['url'], match=match))
                write_to_log = not match

            if write_to_log:
                report.append({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': '{} mismatch'.format('Request' if not request_matched else 'Responses')
                })

            return web.Response(body=await response.text(), status=response.status, headers=response.headers)


async def handle_request(request, mode):
    request_info = await extract_request_info(request)
    # TODO: do we need this?
    request_info['headers']['HOST'] = request.app['TARGET_SERVER_HOST']
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(**request_info) as response:
                latency = getattr(response, 'latency', 0)
                resp = web.Response(body=await response.read(), status=response.status, headers=response.headers)
                logger.debug('Request to {request[url]}: {status}'.format(request=request_info, status=response.status))

        if mode == ZeligMode.SERVER:
            await wait(latency, loop=request.app.loop)
    except UnhandledHTTPRequestError as e:
        request.transport.abort()
        # we have closed a connection but we still need to return something
        raise web.HTTPBadRequest(text=str(e))
    return resp


def start_client(app):
    with Reporter(app['ZELIG_CLIENT_REPORT']) as report:
        # TODO: check this is enough
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate_client(app, loop, report))
        loop.close()


def start_server(app):
    mode = app['ZELIG_MODE']

    if mode == ZeligMode.SERVER:
        record_mode = RecordMode.NONE
    else:
        record_mode = RecordMode.ALL

    # Use ExitStack to optionally enter Reporter context
    with contextlib.ExitStack() as stack:
        cassette = stack.enter_context(vcr.use_cassette(app['ZELIG_CASSETTE_FILE'],
                                       record_mode=record_mode,
                                       match_on=app['REQUEST_MATCH_ON']))
        if mode == ZeligMode.OBSERVER:
            report = stack.enter_context(Reporter(app['ZELIG_OBSERVER_REPORT']))
            # TODO: support http://site.com/path(/)?
            app.router.add_route('*', '/{path:.*}', functools.partial(observe, cassette=cassette, report=report))
        else:
            app.router.add_route('*', '/{path:.*}', functools.partial(handle_request, mode=mode))

        loop = asyncio.get_event_loop()
        handler = app.make_handler(loop=loop)
        f = loop.create_server(handler, app['ZELIG_HOST'], app['ZELIG_PORT'])
        srv = loop.run_until_complete(f)
        print('serving on', srv.sockets[0].getsockname())

        def trigger_shutdown():
            raise KeyboardInterrupt('Loop interrupt')

        loop.add_signal_handler(signal.SIGTERM, trigger_shutdown)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            srv.close()
            loop.run_until_complete(srv.wait_closed())
            loop.run_until_complete(app.shutdown())
            loop.run_until_complete(handler.shutdown(60.0))
            loop.run_until_complete(app.cleanup())
        loop.close()


def main():

    app = web.Application()
    config_app(app)

    logger.info('Start zelig in "{mode}" mode'.format(mode=app['ZELIG_MODE']))
    # Run coroutine for 'client' mode
    # Run server for 'server' and 'proxy' modes
    if app['ZELIG_MODE'] == ZeligMode.CLIENT:
        start_client(app)
    else:
        start_server(app)


if __name__ == '__main__':
    main()
