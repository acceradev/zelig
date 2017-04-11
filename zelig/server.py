import asyncio
import contextlib
import functools
import logging
import signal
import sys

import aiohttp
import vcr
from aiohttp import web
from vcr.errors import UnhandledHTTPRequestError

from zelig import config
from zelig.app import ZeligServerApplication
from zelig.constants import ZeligMode, RecordMode
from zelig.matchers import match_responses
from zelig.report import Reporter
from zelig.utils import (
    extract_response_info, extract_request_info, extract_vcr_request_info, get_response_from_cassette, wait,
    load_cassette, filter_response_headers
)

logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(logging.StreamHandler(sys.stdout))


async def simulate_client(app, loop, report):
    logger.info('Loading cassette {cassette}'.format(cassette=app.config.cassette_file))
    requests, responses = load_cassette(app.config.cassette_file)
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    offset = requests[0].timestamp
    for (request, original_response) in zip(requests, responses):
        await wait(request.timestamp - offset, original_response['latency'], loop=loop)
        request_info = extract_vcr_request_info(request)
        # TODO: handle errors that may occur
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.request(**request_info) as response:
                received_response = await extract_response_info(response)
                match_on = [m.value for m in app.config.response_match_on]
                match = match_responses(original_response, received_response, match_on)
                report.append({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': 'Responses {}'.format('match' if match else 'mismatch')
                })


async def observe(request, cassette, report):
    request_info = await extract_request_info(request)
    original_response = get_response_from_cassette(cassette, request_info)
    request_matched = (original_response is not None)
    write_to_log = not request_matched

    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            received_response = await extract_response_info(response)
            if request_matched:
                # Match responses only when request matched
                matchers = [v.value for v in request.app.config.response_match_on]
                match = match_responses(original_response, received_response, matchers)
                logger.debug('Request to {url}. Responses match: {match}'.format(url=request_info['url'], match=match))
                write_to_log = not match

            if write_to_log:
                report.append({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': '{} mismatch'.format('Request' if not request_matched else 'Responses')
                })

            return web.Response(body=await response.read(), status=response.status,
                                headers=filter_response_headers(response.headers))


async def handle_request(request, mode):
    request_info = await extract_request_info(request)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(**request_info) as response:
                latency = getattr(response, 'latency', 0)
                resp = web.Response(body=await response.read(), status=response.status,
                                    headers=filter_response_headers(response.headers))
                logger.debug('Request to {request[url]}: {status}'.format(request=request_info, status=response.status))

        if mode == ZeligMode.SERVER:
            await wait(latency, loop=request.app.loop)
    except UnhandledHTTPRequestError as e:
        request.transport.abort()
        # we have closed a connection but we still need to return something
        raise web.HTTPBadRequest(text=str(e))
    return resp


def start_client(app):
    with Reporter(app.config.client_report_file) as report:
        # TODO: check this is enough
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate_client(app, loop, report))
        loop.close()


def start_server(app):
    mode = app.config.mode

    if mode == ZeligMode.SERVER:
        record_mode = RecordMode.NONE
    else:
        record_mode = RecordMode.ALL

    # Use ExitStack to optionally enter Reporter context
    with contextlib.ExitStack() as stack:
        request_match_on = [i.value for i in app.config.request_match_on]
        cassette = stack.enter_context(vcr.use_cassette(app.config.cassette_file,
                                                        record_mode=record_mode.value,
                                                        match_on=request_match_on))
        if mode == ZeligMode.OBSERVER:
            report = stack.enter_context(Reporter(app.config.observer_report_file))
            app.router.add_route('*', '/{path:.*}', functools.partial(observe, cassette=cassette, report=report))
        else:
            app.router.add_route('*', '/{path:.*}', functools.partial(handle_request, mode=mode))

        loop = asyncio.get_event_loop()
        handler = app.make_handler(loop=loop)
        f = loop.create_server(handler, app.config.zelig_host, app.config.zelig_port)
        srv = loop.run_until_complete(f)
        print('Serving on', srv.sockets[0].getsockname())

        async def graceful_shutdown():
            srv.close()
            await srv.wait_closed()
            await app.shutdown()
            await handler.shutdown(60.0)
            await app.cleanup()
            print('Shutdown complete')

        loop.add_signal_handler(signal.SIGTERM, loop.stop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(graceful_shutdown())
        loop.close()


def main():
    conf = config.get_config()
    app = ZeligServerApplication(config=conf)

    logger.info('Start zelig in "{mode}" mode'.format(mode=app.config.mode))
    # Run coroutine for 'client' mode
    # Run server for 'server' and 'proxy' modes
    if app.config.mode == ZeligMode.CLIENT:
        start_client(app)
    else:
        start_server(app)


if __name__ == '__main__':
    main()
