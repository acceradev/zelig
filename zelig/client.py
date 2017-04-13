import asyncio

from zelig.log import logger
from zelig.matchers import match_responses
from zelig.report import Reporter
from zelig.utils import load_cassette, extract_vcr_request_info, wait, extract_response_info, make_request


async def simulate_client(config, loop, report):
    logger.info('Loading cassette {cassette}'.format(cassette=config.cassette_file))
    requests, responses = load_cassette(config.cassette_file)
    logger.info('Loaded {n} request-response pairs'.format(n=len(requests)))

    offset = requests[0].timestamp
    for (request, original_response) in zip(requests, responses):
        await wait(request.timestamp - offset, original_response['latency'], loop=loop)

        request_info = extract_vcr_request_info(request)
        response = await make_request(request_info)

        received_response = await extract_response_info(response)

        match_on = [m.value for m in config.response_match_on]
        match = match_responses(original_response, received_response, match_on)
        logger.info(f'Responses match: {match}')

        report.append({
            'request': request_info,
            'original_response': original_response,
            'received_response': received_response,
            'result': 'Responses {}'.format('match' if match else 'mismatch')
        })


def start_client(config):
    with Reporter(config.client_report_file) as report:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(simulate_client(config, loop, report))
        loop.close()
