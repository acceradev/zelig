import asyncio
import time
from urllib.parse import urljoin, urlparse

from multidict import MultiDict
from vcr.errors import UnhandledHTTPRequestError
from vcr.request import Request
from yarl import URL

from report import save_report


class Observer:
    def __init__(self, path):
        self.path = path
        self.data = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        save_report(self.path, self.data)

    def append(self, item):
        self.data.append(item)


async def wait(duration, reserve=0, loop=None):
    # TODO: change name, change params names
    sleep = max(0, duration - reserve)
    await asyncio.sleep(sleep, loop=loop)


async def extract_request_info(request):
    return {
        'method': request.method,
        'url': urljoin(request.app['TARGET_SERVER_BASE_URL'], request.match_info.get('path')),
        # request.query has ProxyMultiDict type which doe not fit vcr aiohttp stub
        'params': MultiDict(request.query),
        'headers': request.headers,
        'data': await request.read(),
    }


def extract_vcr_request_info(request):
    return {
        'method': request.method,
        'url': urlparse(request.uri).geturl(),
        'params': request.query,
        'headers': request.headers,
        'data': request.body,
    }


async def extract_response_info(response):
    # vcr serialize response the same way
    # except of body - vcr user response.text(), however vcr load
    # response from file as bytestring, so we read bytestring for comparison
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
