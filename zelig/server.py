import asyncio
import contextlib
import functools
import logging

import aiohttp
from aiohttp import web

import vcr
from vcr.errors import UnhandledHTTPRequestError
import vcr.serialize
from vcr.serializers import yamlserializer
from vcr.persisters.filesystem import FilesystemPersister

from config import config_app
from constants import ZeligMode, RecordMode
from report import Reporter
from matchers import match_responses
from utils import (
    extract_response_info, extract_request_info, extract_vcr_request_info, get_response_from_cassette, wait
)


logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)


async def simulate_client(app, loop, report):
    logger.info('Loading cassette {cassette}'.format(cassette=app['ZELIG_CASSETTE_FILE']))

    requests, responses = FilesystemPersister.load_cassette(app['ZELIG_CASSETTE_FILE'], yamlserializer)
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
                report({
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
                report({
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
                resp = web.Response(body=await response.text(), status=response.status, headers=response.headers)
                logger.debug('Request to {request[url]}: {status}'.format(request=request_info, status=response.status))

        if mode == ZeligMode.SERVER:
            await wait(latency, loop=request.app.loop)
    except UnhandledHTTPRequestError as e:
        request.transport.abort()
        # TODO: return reasonable response
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
            app.router.add_route('*', '/{path:\w*}', functools.partial(observe, cassette=cassette, report=report))
        else:
            app.router.add_route('*', '/{path:\w*}', functools.partial(handle_request, mode=mode))
        web.run_app(app, host=app['ZELIG_HOST'], port=app['ZELIG_PORT'])


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
    import os
    if 'DEBUG' in os.environ:
        import pydevd
        pydevd.settrace('172.17.0.1', port=9998, stdoutToServer=True, stderrToServer=True)
    main()
