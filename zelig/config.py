import os
from urllib.parse import urlparse

from zelig.constants import RequestMatchCriteria, ZeligMode, ResponseMatchCriteria

__all__ = ['get_config']


def get_config():
    config_class = ConfigFactory.get_config_class()
    config = config_class()
    return config


notset = object()


class ConfigurationError(Exception):
    pass


class MissingValueError(ConfigurationError):
    pass


class InvalidValueError(ConfigurationError):
    pass


class EnvConfigProperty:
    def __init__(self, key, default=notset):
        self._key = key
        self._default = default
        self._value = self.__get_value(key=key, default=default)

    def clean(self, value):
        return value

    @property
    def key(self):
        return self._key

    @property
    def default(self):
        return self._default

    def __get__(self, instance, owner):
        return self._value

    def __get_value(self, default, key):
        self.__check_has_value()
        value = os.environ.get(key, default=default)
        return self.clean(value)

    def __check_has_value(self):
        if self.key not in os.environ and self.default is notset:
            error_msg = f'You should set \'{self.key}\' environment variable'
            raise MissingValueError(error_msg)


class IntProperty(EnvConfigProperty):
    def clean(self, value):
        try:
            return int(value)
        except TypeError:
            raise InvalidValueError(f'Value of {self.key} param should be integer')


class EnumProperty(EnvConfigProperty):
    def __init__(self, key, enum_class, default=notset):
        self.enum_class = enum_class
        super().__init__(key=key, default=default)

    def clean(self, value):
        try:
            return self.enum_class(value)
        except ValueError:
            possible_values = ', '.join((f'{c.value}' for c in self.enum_class))
            raise InvalidValueError(f'Value of {self.key} param should be one of [{possible_values}]')


class MultiEnumProperty(EnumProperty):
    def clean(self, value):
        res = []
        for v in value.split():
            res.append(super().clean(v))

        if not res:
            raise InvalidValueError(
                f'Value of {self.key} param should be one or more (space separated) of [{possible_values}]')
        return res


class BaseConfig:
    DEFAULT_REQUEST_MATCH_ON = ' '.join((cr.value for cr in RequestMatchCriteria))
    DEFAULT_RESPONSE_MATCH_ON = ' '.join((cr.value for cr in ResponseMatchCriteria))

    mode = notset
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)
    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)

    target_server_base_url = EnvConfigProperty('TARGET_SERVER_BASE_URL')

    @property
    def target_server_host(self):
        res = urlparse(self.target_server_base_url).netloc
        return res


class ClientConfig(BaseConfig):
    mode = ZeligMode.CLIENT
    cassette_file = EnvConfigProperty('ZELIG_CASSETTE_FILE', default='cassette.yml')
    client_report_file = EnvConfigProperty('ZELIG_CLIENT_REPORT', default='client_report.yml')


class BaseWebServerConfig(BaseConfig):
    cassette_file = EnvConfigProperty('ZELIG_CASSETTE_FILE', default='cassette.yml')
    zelig_host = EnvConfigProperty('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)


class ProxyConfig(BaseWebServerConfig):
    mode = ZeligMode.PROXY


class ServerConfig(BaseWebServerConfig):
    mode = ZeligMode.SERVER


class ObserverConfig(BaseWebServerConfig):
    mode = ZeligMode.OBSERVER

    observer_report_file = EnvConfigProperty('ZELIG_OBSERVER_REPORT', default='observer_report.yml')


class ConfigFactory:
    mode = EnumProperty('ZELIG_MODE', enum_class=ZeligMode)

    MAPPING = {
        ZeligMode.CLIENT: ClientConfig,
        ZeligMode.SERVER: ServerConfig,
        ZeligMode.PROXY: ProxyConfig,
        ZeligMode.OBSERVER: ObserverConfig,
    }

    @classmethod
    def get_config_class(cls):
        return cls.MAPPING[cls.mode]

        # def config_app(app):
        #     app['ZELIG_MODE'] = os.environ.get('ZELIG_MODE', ZeligMode.PROXY)
        #
        #     # TODO: use enum
        #     assert app['ZELIG_MODE'] in ('proxy', 'server', 'client', 'observer'), \
        #         'ZELIG_MODE should be one of "proxy", "observer", "server" or "client"'
        #
        #     app['TARGET_SERVER_BASE_URL'] = os.environ.get('TARGET_SERVER_BASE_URL', 'http://www.httpbin.org')
        #     app['TARGET_SERVER_HOST'] = urlparse(app['TARGET_SERVER_BASE_URL']).netloc
        #
        #     app['ZELIG_CASSETTE_FILE'] = os.environ.get('ZELIG_CASSETTE_FILE', 'cassette.yml')
        #     app['ZELIG_CLIENT_REPORT'] = os.environ.get('ZELIG_CLIENT_REPORT', 'client_report.yml')
        #     app['ZELIG_OBSERVER_REPORT'] = os.environ.get('ZELIG_OBSERVER_REPORT', 'observer_report.yml')
        #
        #     app['ZELIG_HOST'] = os.environ.get('ZELIG_HOST', '0.0.0.0')
        #     app['ZELIG_PORT'] = int(os.environ.get('ZELIG_PORT', 8081))
        #
        #     app['REQUEST_MATCH_ON'] = ['method', 'scheme', 'host', 'port', 'path', 'query', 'body']
        #     app['RESPONSE_MATCH_ON'] = ['body', 'status']
