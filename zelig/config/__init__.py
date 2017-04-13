from .factory import ConfigFactory
from .errors import ConfigurationError


__all__ = ['get_config', 'ConfigurationError']


def get_config():
    config_class = ConfigFactory.get_config_class()
    cfg = config_class()
    return cfg


