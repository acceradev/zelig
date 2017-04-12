import asyncio
import contextlib
import functools
import logging
import signal

from aiohttp import web
import vcr
from vcr.errors import UnhandledHTTPRequestError

from zelig.app import ZeligServerApplication
from zelig.constants import ZeligMode, RecordMode
from zelig.matchers import match_responses
from zelig.report import Reporter
from zelig.utils import (
    extract_response_info, extract_request_info, get_response_from_cassette, wait,
    make_request, get_server_response
)

logger = logging.getLogger('zelig')


async def observer(request, report, cassette):
    request_info = await extract_request_info(request)
    original_response = get_response_from_cassette(cassette, request_info)
    request_matched = (original_response is not None)
    write_to_log = not request_matched

    response = await make_request(request_info)
    received_response = await extract_response_info(response)
    logger.info(f'Request already exist: {request_matched}')
    if request_matched:
        # Match responses only when request matched
        matchers = [v.value for v in request.app.config.response_match_on]
        match = match_responses(original_response, received_response, matchers)
        logger.info(f'Responses match: {match}')
        write_to_log = not match

    if write_to_log:
        report.append({
            'request': request_info,
            'original_response': original_response,
            'received_response': received_response,
            'result': '{} mismatch'.format('Request' if not request_matched else 'Responses')
        })
    return await get_server_response(response)


async def proxy(request):
    request_info = await extract_request_info(request)
    response = await make_request(request_info)
    return await get_server_response(response)

async def server(request):
    request_info = await extract_request_info(request)
    response = await make_request(request_info)
    await wait(response.latency, loop=request.app.loop)
    return await get_server_response(response)


async def request_handler(request, mode):
    handlers = {
        ZeligMode.SERVER: server,
        ZeligMode.PROXY: proxy
    }
    try:
        return await handlers[mode](request)
    except UnhandledHTTPRequestError as e:
        logger.warning(f'Unknown request in {mode.value} mode: {request.method} {request.url}')
        request.transport.abort()
        # we have closed a connection but we still need to return something
        raise web.HTTPBadRequest(text=str(e))


def start(app):
    loop = asyncio.get_event_loop()
    handler = app.make_handler(loop=loop)
    f = loop.create_server(handler, app.config.zelig_host, app.config.zelig_port)
    srv = loop.run_until_complete(f)
    logging.info('Serving on', srv.sockets[0].getsockname())

    async def graceful_shutdown():
        srv.close()
        await srv.wait_closed()
        await app.shutdown()
        await handler.shutdown(60.0)
        await app.cleanup()
        logger.info('Zelig server successfully shut down')

    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(graceful_shutdown())
    loop.close()


def start_server(config):
    app = ZeligServerApplication(config=config)
    mode = config.mode

    if mode == ZeligMode.SERVER:
        record_mode = RecordMode.NONE
    else:
        record_mode = RecordMode.ALL

    # Use ExitStack to optionally enter Reporter context
    with contextlib.ExitStack() as stack:
        request_match_on = [i.value for i in config.request_match_on]
        cassette = stack.enter_context(vcr.use_cassette(config.cassette_file,
                                                        record_mode=record_mode.value,
                                                        match_on=request_match_on))
        if mode == ZeligMode.OBSERVER:
            report = stack.enter_context(Reporter(config.observer_report_file))
            app.router.add_route('*', '/{path:.*}', functools.partial(observer, cassette=cassette, report=report))
        else:
            app.router.add_route('*', '/{path:.*}', functools.partial(request_handler, mode=mode))

        start(app)
