import asyncio

import aiohttp

from zelig.log import logger
from zelig.matchers import match_responses
from zelig.report import Reporter
from zelig.utils import (
    load_cassette, extract_vcr_request_info, wait, extract_response_info, extract_error_response_info, get_query_string
)


async def playback(config, loop, report):
    logger.info('Loading cassette {cassette}'.format(cassette=config.cassette_file))
    requests, responses = load_cassette(config.cassette_file)
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    async with aiohttp.ClientSession() as session:
        offset = requests[0].timestamp
        for (request, original_response) in zip(requests, responses):
            await wait(request.timestamp - offset, original_response['latency'], loop=loop)
            offset = request.timestamp

            request_info = extract_vcr_request_info(request)
            try:
                async with session.request(**request_info) as response:
                    qs = get_query_string(request_info['params'])
                    logger.info('{request[method]} {request[url]}{qs} - {status}'.format(
                        request=request_info, status=response.status, qs=qs))
                    received_response = await extract_response_info(response)
            except aiohttp.ClientError as e:
                received_response = extract_error_response_info(request_info, e)

            match_on = [m.value for m in config.response_match_on]
            match = match_responses(original_response, received_response, match_on)
            logger.info(f'Responses match: {match}')
            if not match:
                report.append({
                    'request': request_info,
                    'original_response': original_response,
                    'received_response': received_response,
                    'result': 'Responses {}'.format('match' if match else 'mismatch')
                })


def start_playback(config):
    with Reporter(config.playback_report_file) as report:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(playback(config, loop, report))
        loop.close()
