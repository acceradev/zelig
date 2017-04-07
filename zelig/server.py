import pydevd
import logging
import time

import aiohttp
from aiohttp import web
import asyncio

import vcr
import vcr.serialize

from config import config_app
from constants import ZeligMode, RecordMode
from pathces import monkey_patch
from report import save_client_report, get_report
from utils import (
    extract_response_info, extract_request_info, extract_vcr_request_info, get_response_from_cassette,
    Timer, Observer, wait
)


logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)


async def simulate_client(app, loop):
    logger.info('Loading cassette {cassette}'.format(cassette=app['ZELIG_CASSETTE_FILE']))
    # TODO: use load_cassette from vcr's master
    with vcr.use_cassette(app['ZELIG_CASSETTE_FILE'],
                          record_mode=RecordMode.NONE) as cass:
        requests, responses = cass.requests, cass.responses
    if not (requests and responses):
        raise web.HTTPError(text='Can not load a cassette')
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    match_results = []
    for (request, original_response) in zip(requests, responses):
        await wait(request.offset, original_response['latency'], loop)

        request_info = extract_vcr_request_info(request)
        # TODO: handle errors that may occur
        async with aiohttp.ClientSession(loop=loop) as session:
            async with session.request(**request_info) as response:
                response_info = await extract_response_info(response)
                # TODO: move to const
                report = get_report(request_info, original_response, response_info, app['RESPONSE_MATCH_ON'])
                match_results.append(report)
    save_client_report(app['ZELIG_CLIENT_REPORT'], match_results)


async def observe(request, cassette, observer):
    # TODO: check if it matches request under the hood and we can extract this info
    request_info = await extract_request_info(request)
    original_response = get_response_from_cassette(cassette, request_info)

    request_matched = (original_response is not None)
    if not request_matched:
        observer.append({
            'reason': 'Request mismatch',
            'request': request_info,
            # TODO: find a workaround
            'original_response': {},
            'received_response': {}
        })

    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            # Match response here
            if request_matched:
                response_info = await extract_response_info(response)
                # TODO: move to const
                responses_log = get_report(request_info, original_response, response_info,
                                           request.app['RESPONSE_MATCH_ON'])
                if not responses_log['match']:
                    log = responses_log
                    log['reason'] = 'Responses mismatch'
                    observer.append(log)
            return web.Response(body=await response.text(), status=response.status, headers=response.headers)


async def proxy(request):
    request_info = await extract_request_info(request)
    # TODO: do we need this?
    request_info['headers']['HOST'] = request.app['TARGET_SERVER_HOST']
    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            return web.Response(body=await response.text(), status=response.status, headers=response.headers)


async def handle_request(request):
    # Disable possibility to change cassette by default
    mode = request.app['ZELIG_MODE'].lower()

    if mode == ZeligMode.SERVER:
        record_mode = RecordMode.NONE
    else:
        record_mode = RecordMode.ALL
    with vcr.use_cassette(request.app['ZELIG_CASSETTE_FILE'],
                          record_mode=record_mode,
                          match_on=request.app['REQUEST_MATCH_ON']) as cassette:
        if mode == ZeligMode.OBSERVER:
            try:
                with Observer(request.app['ZELIG_OBSERVER_REPORT']) as observer:
                    with Timer(request.app) as timer:
                        response = await observe(request, cassette, observer)
            except Exception as e:
                print(e)
                return
        else:
            with Timer(request.app) as timer:
                response = await proxy(request)
        if mode == ZeligMode.SERVER:
            # TODO: find a better way
            # TODO: will not work - it's time of vcr - not real response
            await asyncio.sleep(timer.latency)
        else:
            # TODO: find a better way
            cassette.requests[-1].offset = timer.offset
            cassette.responses[-1]['latency'] = timer.latency
    # TODO: check if we need to catch exceptions
    # possibly no, cause aiohttp vcr stub simply set 599 status code to response
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
        loop.run_until_complete(simulate_client(app, loop))
        loop.close()
    else:
        # TODO: support http://site.com/path(/)?
        app.router.add_route('*', '/{path:\w*}', handle_request)
        web.run_app(app, host=app['ZELIG_HOST'], port=app['ZELIG_PORT'])


if __name__ == '__main__':
    pydevd.settrace('172.17.0.1', port=9998, stdoutToServer=True, stderrToServer=True)
    patch, restore = monkey_patch()
    patch()
    start = time.time()
    main()
    restore()
