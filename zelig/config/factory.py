from .properties import EnumProperty
from .configs import PlaybackConfig, ServeConfig, RecordConfig, ObserveConfig

from zelig.constants import ZeligMode


class ConfigFactory:
    mode = EnumProperty('ZELIG_MODE', enum_class=ZeligMode)

    MAPPING = {
        ZeligMode.PLAYBACK: PlaybackConfig,
        ZeligMode.SERVE: ServeConfig,
        ZeligMode.RECORD: RecordConfig,
        ZeligMode.OBSERVE: ObserveConfig,
    }

    @classmethod
    def get_config_class(cls):
        return cls.MAPPING[cls.mode]
