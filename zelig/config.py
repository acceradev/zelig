import os
from urllib.parse import urlparse

from constants import ZeligMode


def create_config():
    config = {
        'mode': os.environ.get('ZELIG_MODE', ZeligMode.PROXY),
        'target_server_base_url': os.environ.get('TARGET_SERVER_BASE_URL', 'http://www.httpbin.org'),
        'cassette_path': os.environ.get('ZELIG_CASSETTE_FILE', 'cassette.yml'),
        'client_report_path': os.environ.get('ZELIG_CLIENT_REPORT', 'client_report.yml'),
        'observer_report_path': os.environ.get('ZELIG_OBSERVER_REPORT', 'observer_report.yml'),
        'host': os.environ.get('ZELIG_HOST', '0.0.0.0'),
        'port': int(os.environ.get('ZELIG_PORT', 8081)),
        'requests_match_on': ['method', 'scheme', 'host', 'port', 'path', 'query', 'body'],
        'responses_match_on': ['body', 'status']
    }

    return Config(config)


class Config:
    def __init__(self, config):
        assert config['mode'] in ('proxy', 'server', 'client', 'observer')
        for key, value in config.items():
            setattr(self, key, value)

        self.target_server_host = urlparse(self.target_server_base_url).netloc
