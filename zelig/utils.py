from urllib.parse import urljoin, urlparse

from multidict import MultiDict


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