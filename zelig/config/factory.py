from .properties import EnumProperty
from .configs import ClientConfig, ServerConfig, ProxyConfig, ObserverConfig

from zelig.constants import ZeligMode


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
