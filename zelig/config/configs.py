from urllib.parse import urlparse

from zelig.constants import RequestMatchCriteria, ZeligMode, ResponseMatchCriteria
from .properties import Property, IntProperty, MultiEnumProperty

DEFAULT_REQUEST_MATCH_ON = ' '.join((cr.value for cr in RequestMatchCriteria))
DEFAULT_RESPONSE_MATCH_ON = ' '.join((cr.value for cr in ResponseMatchCriteria))


class BaseConfig:
    mode = None
    cassette_file = Property('ZELIG_CASSETTE_FILE', default='cassette.yml')
    target_server_base_url = Property('TARGET_SERVER_BASE_URL')

    @property
    def target_server_host(self):
        res = urlparse(self.target_server_base_url).netloc
        return res


class ClientConfig(BaseConfig):
    mode = ZeligMode.CLIENT
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)
    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)
    client_report_file = Property('ZELIG_CLIENT_REPORT', default='client_report.yml')


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
    mode = ZeligMode.SERVER
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)
    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)
    observer_report_file = Property('ZELIG_OBSERVER_REPORT', default='observer_report.yml')
