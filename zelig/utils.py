import asyncio
from urllib.parse import urljoin, urlparse

from multidict import MultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.request import Request
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serializers import yamlserializer
from yarl import URL


async def wait(duration, reserve=0, loop=None):
    # TODO: change name, change params names
    sleep = max(0, duration - reserve)
    await asyncio.sleep(sleep, loop=loop)


async def extract_request_info(request):
    request_info = {
        'method': request.method,
        'url': urljoin(request.app.config.target_server_base_url, request.match_info.get('path')),
        # request.query has ProxyMultiDict type which doe not fit vcr aiohttp stub
        'params': MultiDict(request.query),
        'headers': request.headers,
        'data': await request.read(),
    }
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


def get_response_from_cassette(cassette, request_info):
    request = Request(method=request_info['method'],
                      uri=str(URL(request_info['url']).with_query(request_info['params'])),
                      body=request_info['data'],
                      headers=request_info['headers'])
    # TODO: define function that will return first response for request
    try:
        responses = cassette.responses_of(request)
    except UnhandledHTTPRequestError:
        return None
    return responses[0]


def load_cassette(path):
    return FilesystemPersister.load_cassette(path, yamlserializer)


def filter_response_headers(headers, filtered_headers=('content-encoding', 'content-length')):
    return {k: v for k, v in headers.items() if k.lower() not in filtered_headers}
