import asyncio
import urllib.parse
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import web
from multidict import MultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.persisters.filesystem import FilesystemPersister
from vcr.request import Request
from vcr.serializers import yamlserializer
from yarl import URL

from zelig.constants import HEADERS_TO_IGNORE, ErrorCodes
from zelig.log import logger


async def wait(duration, reserve=0, loop=None):
    sleep = max(0, duration - reserve)
    logger.debug(f'Processing simulation: sleeping {sleep} seconds')
    await asyncio.sleep(sleep, loop=loop)


async def extract_request_info(request, replace_host=True):
    request_info = {
        'method': request.method,
        'url': urljoin(request.app.config.target_server_base_url, request.match_info.get('path')),
        # request.query has ProxyMultiDict type which doe not fit vcr aiohttp stub
        'params': MultiDict(request.query),
        'headers': request.headers,
        'data': await request.read(),
    }
    if replace_host:
        request_info['headers']['HOST'] = request.app.config.target_server_host
    return request_info


def extract_vcr_request_info(request):
    parsed_url = urlparse(request.uri)
    url = urljoin('{}://{}'.format(parsed_url.scheme, parsed_url.netloc), parsed_url.path)
    return {
        'method': request.method,
        'url': url,
        'params': request.query,
        'headers': request.headers,
        'data': request.body,
    }


async def extract_response_info(response):
    return {
        'status': {
            'code': response.status,
            'message': response.reason,
        },
        'headers': dict(response.headers),
        'body': {'string': (await response.read())},
        'url': response.url,
    }


def extract_error_response_info(request_info, error):
    return {
        'status': {
            'code': ErrorCodes.RequestError.value,
            'message': str(error),
            'error': str(error.__class__)
        },
        'headers': {},
        'body': {'string': str(error)},
        'url': request_info['url'],
    }


def get_response_from_data(data, request_info):
    request = Request(method=request_info['method'],
                      uri=str(URL(request_info['url']).with_query(request_info['params'])),
                      body=request_info['data'],
                      headers=request_info['headers'])
    try:
        responses = data.responses_of(request)
    except UnhandledHTTPRequestError:
        return None
    return responses[0]


def load_data(path):
    return FilesystemPersister.load_cassette(path, yamlserializer)


def filter_response_headers(headers):
    filtered_headers = [h.lower() for h in HEADERS_TO_IGNORE]
    return {k: v for k, v in headers.items() if k.lower() not in filtered_headers}


async def get_server_response(response):
    return web.Response(body=await response.read(), status=response.status,
                        headers=filter_response_headers(response.headers))


def get_query_string(query_params):
    return f'?{urllib.parse.urlencode(query_params)}' if query_params else ''


async def make_request(request_info):
    async with aiohttp.ClientSession() as session:
        async with session.request(**request_info) as response:
            qs = get_query_string(request_info['params'])
            logger.info('{request[method]} {request[url]}{qs} - {status}'.format(
                request=request_info, status=response.status, qs=qs))

            return response
