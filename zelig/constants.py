from enum import Enum, IntEnum, unique


@unique
class ZeligMode(Enum):
    RECORD = 'record'
    SERVE = 'serve'
    PLAYBACK = 'playback'
    OBSERVE = 'observe'


@unique
class RecordMode(Enum):
    NONE = 'none'
    ONCE = 'once'
    NEW_EPISODES = 'new_episodes'
    ALL = 'all'


@unique
class RequestMatchCriteria(Enum):
    METHOD = 'method'
    SCHEME = 'scheme'
    HOST = 'host'
    PORT = 'port'
    PATH = 'path'
    QUERY = 'query'
    BODY = 'body'


@unique
class ResponseMatchCriteria(Enum):
    BODY = 'body'
    STATUS = 'status'


@unique
class ErrorCodes(IntEnum):
    RequestError = 490


HEADERS_TO_IGNORE = ['Content-Encoding', 'Content-Length', 'Transfer-Encoding', 'Trailer']
