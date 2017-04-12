from zelig.config.factory import ConfigFactory

__all__ = ['get_config']


def get_config():
    config_class = ConfigFactory.get_config_class()
    cfg = config_class()
    return cfg


