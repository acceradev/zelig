import contextlib
import functools
import logging


import aiohttp
from aiohttp import web
import asyncio

import vcr
import vcr.serialize
from vcr.serializers import yamlserializer
from vcr.persisters.filesystem import FilesystemPersister

from config import config_app
from constants import ZeligMode, RecordMode
from report import save_report
from matchers import match_responses
from utils import (
    extract_response_info, extract_request_info, extract_vcr_request_info, get_response_from_cassette, Observer, wait
)


logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)


async def simulate_client(app, loop):
    logger.info('Loading cassette {cassette}'.format(cassette=app['ZELIG_CASSETTE_FILE']))

    requests, responses = FilesystemPersister.load_cassette(app['ZELIG_CASSETTE_FILE'], yamlserializer)
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    match_results = []
    offset = requests[0].timestamp
    for (request, original_response) in zip(requests, responses):
        # TODO: check if we need this formula
        await wait(request.timestamp - offset, original_response['latency'], loop=loop)
        request_info = extract_vcr_request_info(request)
        # TODO: handle errors that may occur
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.request(**request_info) as response:
                received_response = await extract_response_info(response)
                match = match_responses(original_response, received_response, app['RESPONSE_MATCH_ON'])
                match_results.append({
                    'request': request,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': 'Responses {}'.format('match' if match else 'mismatch')
                })
    # TODO: move save somewhere else
    save_report(app['ZELIG_CLIENT_REPORT'], match_results)


async def observe(request, cassette, observer):
    request_info = await extract_request_info(request)
    original_response = get_response_from_cassette(cassette, request_info)
    received_response = None
    request_matched = (original_response is not None)
    write_to_log = not request_matched

    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            # Match response here
            if request_matched:
                # Match responses only when request matched
                received_response = await extract_response_info(response)
                match = not match_responses(original_response, received_response, request.app['RESPONSE_MATCH_ON'])
                logger.debug('Request to {url}. Responses match: {match}'.format(url=request_info['url'], match=match))
                write_to_log = not match

            if write_to_log:
                observer.append({
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
    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            # For now we have a case when client asks for new url during server-mode
            # The response then do not have a 'latency'
            latency = getattr(response, 'latency', 0)
            resp = web.Response(body=await response.text(), status=response.status, headers=response.headers)
            logger.debug('Request to {request[url]}: {status}'.format(request=request_info, status=response.status))

    if mode == ZeligMode.SERVER:
        # TODO: find a better way
        await wait(latency, loop=request.app.loop)
    # TODO: check if we need to catch exceptions
    # possibly no, cause aiohttp vcr stub simply set 599 status code to response
    return resp


def start_server(app):
    mode = app['ZELIG_MODE']

    if mode == ZeligMode.SERVER:
        record_mode = RecordMode.NONE
    else:
        record_mode = RecordMode.ALL

    with contextlib.ExitStack() as stack:
        cassette = stack.enter_context(vcr.use_cassette(app['ZELIG_CASSETTE_FILE'],
                                       record_mode=record_mode,
                                       match_on=app['REQUEST_MATCH_ON']))
        if mode == ZeligMode.OBSERVER:
            observer = stack.enter_context(Observer(app['ZELIG_OBSERVER_REPORT']))
            # TODO: support http://site.com/path(/)?
            app.router.add_route('*', '/{path:\w*}', functools.partial(observe, cassette=cassette, observer=observer))
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
        # TODO: check this is enough
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate_client(app, loop))
        loop.close()
    else:
        start_server(app)


if __name__ == '__main__':
    import os
    if 'DEBUG' in os.environ:
        import pydevd
        pydevd.settrace('172.17.0.1', port=9998, stdoutToServer=True, stderrToServer=True)
    main()
