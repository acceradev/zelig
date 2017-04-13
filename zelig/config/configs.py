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
        self.__perform_check()

    @property
    def target_server_host(self):
        res = urlparse(self.target_server_base_url).netloc
        return res

    @property
    def cassette_file(self):
        return os.path.join(self.base_files_dir, self.cassette_name)

    def __perform_check(self):
        for k in dir(self):
            if not k.startswith('__'):
                getattr(self, k)


class PlaybackConfig(BaseConfig):
    mode = ZeligMode.PLAYBACK
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)
    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)

    playback_report_name = Property('ZELIG_PLAYBACK_REPORT', default='playback_report.yml')

    @property
    def playback_report_file(self):
        return os.path.join(self.base_files_dir, self.playback_report_name)


class RecordConfig(BaseConfig):
    mode = ZeligMode.RECORD
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)

    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)


class ServeConfig(BaseConfig):
    mode = ZeligMode.SERVE
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)
    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)


class ObserveConfig(BaseConfig):
    mode = ZeligMode.OBSERVE
    zelig_host = Property('ZELIG_HOST', default='0.0.0.0')
    zelig_port = IntProperty('ZELIG_PORT', default=8081)

    request_match_on = MultiEnumProperty('REQUEST_MATCH_ON', enum_class=RequestMatchCriteria,
                                         default=DEFAULT_REQUEST_MATCH_ON)

    response_match_on = MultiEnumProperty('RESPONSE_MATCH_ON', enum_class=ResponseMatchCriteria,
                                          default=DEFAULT_RESPONSE_MATCH_ON)
    observe_report_name = Property('ZELIG_OBSERVE_REPORT', default='observe_report.yml')

    @property
    def observe_report_file(self):
        return os.path.join(self.base_files_dir, self.observe_report_name)
