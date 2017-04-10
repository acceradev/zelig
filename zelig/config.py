import os
from urllib.parse import urlparse

from constants import ZeligMode


def config_app(app):
    app['ZELIG_MODE'] = os.environ.get('ZELIG_MODE', ZeligMode.PROXY)

    # TODO: use enum
    assert app['ZELIG_MODE'] in ('proxy', 'server', 'client', 'observer'), \
        'ZELIG_MODE should be one of "proxy", "observer", "server" or "client"'

    app['TARGET_SERVER_BASE_URL'] = os.environ.get('TARGET_SERVER_BASE_URL', 'http://172.17.0.1:8000')
    app['TARGET_SERVER_HOST'] = urlparse(app['TARGET_SERVER_BASE_URL']).netloc

    # TODO: rename default
    app['ZELIG_CASSETTE_FILE'] = os.environ.get('ZELIG_CASSETTE_FILE', 'cassette.yml')
    app['ZELIG_CLIENT_REPORT'] = os.environ.get('ZELIG_CLIENT_REPORT', 'client_report.yml')
    app['ZELIG_OBSERVER_REPORT'] = os.environ.get('ZELIG_OBSERVER_REPORT', 'observer_report.yml')

    app['ZELIG_HOST'] = os.environ.get('ZELIG_HOST', '0.0.0.0')
    app['ZELIG_PORT'] = int(os.environ.get('ZELIG_PORT', 8081))

    app['REQUEST_MATCH_ON'] = ['method', 'scheme', 'host', 'port', 'path', 'query', 'body']
    app['RESPONSE_MATCH_ON'] = ['body', 'status']

