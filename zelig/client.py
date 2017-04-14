import asyncio

import aiohttp

from zelig.log import logger
from zelig.matchers import match_responses
from zelig.report import Reporter
from zelig.utils import (
    load_cassette, extract_vcr_request_info, wait, extract_response_info, extract_error_response_info, get_query_string
)


async def playback(config, loop, reporter):
    logger.info('Loading cassette {cassette}'.format(cassette=config.cassette_directory))
    try:
        requests, responses = load_cassette(config.cassette_directory)
    except ValueError as e:
        logger.warning(f'Error while loading cassette: {str(e)}')
        return
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    async with aiohttp.ClientSession() as session:
        offset = requests[0].timestamp
        for (i, (request, original_response)) in enumerate(zip(requests, responses), 1):
            await wait(request.timestamp - offset, original_response['latency'], loop=loop)
            offset = request.timestamp

            request_info = extract_vcr_request_info(request)
            try:
                async with session.request(**request_info) as response:
                    logger.info('{request[method]} {request[url]}{qs} - {status}'.format(
                        request=request_info, status=response.status, qs=get_query_string(request_info['params'])))
                    received_response = await extract_response_info(response)
            except aiohttp.ClientError as e:
                logger.warning('{request[method]} {request[url]}{qs} - Failed: {error}'.format(
                    request=request_info, qs=get_query_string(request_info['params']), error=str(e)))
                received_response = extract_error_response_info(request_info, e)

            match_on = [m.value for m in config.response_match_on]
            match = match_responses(original_response, received_response, match_on)
            logger.info(f'Responses match: {match}')
            if not match:
                reporter.report({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': 'Responses {}'.format('match' if match else 'mismatch')
                }, number=i)
            reporter.record_metadata()


def start_playback(config):
    with Reporter(config.playback_report_directory) as reporter:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(playback(config, loop, reporter))
        loop.close()
