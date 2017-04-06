import pydevd
import logging
import time

import aiohttp
from aiohttp import web
import asyncio
from yarl import URL

import vcr
from vcr.request import Request
import vcr.serialize

from config import config_app
from constants import ZeligMode, RecordMode
from matchers import match_responses
from pathces import monkey_patch
from report import create_report
from utils import extract_response_info, extract_request_info, extract_vcr_request_info


logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)


async def imitate_client(app, loop):
    logger.info('Loading cassette {cassette}'.format(cassette=app['ZELIG_CASSETTE_FILE']))
    with vcr.use_cassette(app['ZELIG_CASSETTE_FILE'],
                          record_mode=RecordMode.NONE) as cass:
        requests, responses = cass.requests, cass.responses
    if not (requests and responses):
        raise web.HTTPError(text='Can not load a cassette')
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    match_results = []
    offset = requests[0].offset
    for (request, original_response) in zip(requests, responses):
        # TODO: check if we need this formula
        sleep = int(max(0, request.offset - offset - original_response['latency']))
        asyncio.sleep(sleep, loop=loop)
        offset = request.offset
        request_info = extract_vcr_request_info(request)
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.request(**request_info) as response:
                response_info = await extract_response_info(response)
                match = match_responses(original_response, response_info, ['body', 'status'])
                match_results.append({
                    'url': request.uri,
                    'original_response': original_response,
                    'received_response': response_info,
                    'result': match
                })
                logger.debug('Request to {url}. Responses match: {match}'.format(url=request.uri, match=match))
    create_report(app['ZELIG_CLIENT_REPORT'], match_results)


def get_response_latency(cassette, request_info):
    request = Request(method=request_info['method'],
                      uri=URL(request_info['url']).with_query(request_info['params']),
                      body=request_info['data'],
                      headers=request_info['headers'])
    responses = cassette.responses_of(request)
    return responses[0]['latency']


async def proxy(request, recording, cassette):
    request_info = await extract_request_info(request)
    # TODO: do we need this?
    request_info['headers']['HOST'] = request.app['TARGET_SERVER_HOST']
    async with aiohttp.ClientSession() as session:
        if recording:
            if 'START' not in request.app:
                request.app['START'] = time.perf_counter()

            request_offset = time.perf_counter() - request.app['START']
            start_time = time.perf_counter()
        else:
            request_offset = 0
        async with session.request(**request_info) as response:
            # TODO: replace 0
            latency = (time.perf_counter() - start_time) if recording else 0
            logger.debug('Request to {request[url]}: {status} in {latency}'.format(
                request=request_info, status=response.status, latency=latency))
            return (
                web.Response(body=await response.text(), status=response.status, headers=response.headers),
                latency,
                request_offset
            )


async def handle_request(request):
    # Disable possibility to change cassette by default
    mode = request.app['ZELIG_MODE']

    if mode == ZeligMode.PROXY:
        record_mode = RecordMode.ALL
        recording = True
    else:
        record_mode = RecordMode.NONE
        recording = False
    try:
        with vcr.use_cassette(request.app['ZELIG_CASSETTE_FILE'],
                              record_mode=record_mode,
                              match_on=request.app['REQUEST_MATCH_ON']) as cassette:
            response, latency, request_offset = await proxy(request, recording, cassette)
            if mode == ZeligMode.PROXY:
                # TODO: find a better way
                cassette.requests[-1].offset = request_offset
                cassette.responses[-1]['latency'] = latency
            else:
                # TODO: find a better way
                asyncio.sleep(latency)
        # TODO: check if we need to catch exceptions
        # possibly no, cause aiohttp vcr stub simply set 599 status code to response
    except Exception as e:
        print(e)
        return
    return response


def main():
    app = web.Application()
    config_app(app)

    logger.info('Start zelig in "{mode}" mode'.format(mode=app['ZELIG_MODE']))
    # Run coroutine for 'client' mode
    # Run server for 'server' and 'proxy' modes
    if app['ZELIG_MODE'] == ZeligMode.CLIENT:
        # TODO: check this is enough
        loop = asyncio.get_event_loop()
        loop.run_until_complete(imitate_client(app, loop))
        loop.close()
    else:
        # TODO: support http://site.com/path(/)?
        app.router.add_route('*', '/{path:\w*}', handle_request)
        web.run_app(app, host=app['ZELIG_HOST'], port=app['ZELIG_PORT'])


if __name__ == '__main__':
    # pydevd.settrace('172.17.0.1', port=9998, stdoutToServer=True, stderrToServer=True)
    patch, restore = monkey_patch()
    patch()
    start = time.time()
    main()
    print(time.time() - start)
    restore()
