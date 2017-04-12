from urllib.parse import urlparse
import os

from zelig.constants import RequestMatchCriteria, ZeligMode, ResponseMatchCriteria
from .properties import Property, IntProperty, MultiEnumProperty, PathProperty

DEFAULT_REQUEST_MATCH_ON = ' '.join((cr.value for cr in RequestMatchCriteria))
DEFAULT_RESPONSE_MATCH_ON = ' '.join((cr.value for cr in ResponseMatchCriteria))


class BaseConfig:
    mode = None
    base_files_dir = PathProperty('/files')
    cassette_name = Property('ZELIG_CASSETTE_FILE', default='cassette.yml')
    target_server_base_url = Property('TARGET_SERVER_BASE_URL')

    def __init__(self):
        for k in dir(self):
            if not k.startswith('__'):
                getattr(self, k)

    @property
    def target_server_host(self):
        res = urlparse(self.target_server_base_url).netloc
        return res

    @property
    def cassette_file(self):
        return os.path.join(self.base_files_dir, self.cassette_name)


class ClientConfig(BaseConfig):
    mode = ZeligMode.CLIENT
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)
    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)

    client_report_name = Property('ZELIG_CLIENT_REPORT', default='client_report.yml')

    @property
    def client_report_file(self):
        return os.path.join(self.base_files_dir, self.client_report_name)


class ProxyConfig(BaseConfig):
    mode = ZeligMode.PROXY
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)

    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)


class ServerConfig(BaseConfig):
    mode = ZeligMode.SERVER
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)


class ObserverConfig(BaseConfig):
    mode = ZeligMode.OBSERVER
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)

    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)

    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)
    observer_report_name = Property('ZELIG_OBSERVER_REPORT', default='observer_report.yml')

    @property
    def observer_report_file(self):
        return os.path.join(self.base_files_dir, self.observer_report_name)
