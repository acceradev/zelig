from enum import Enum, unique


@unique
class ZeligMode(Enum):
    PROXY = 'proxy'
    SERVER = 'server'
    CLIENT = 'client'
    OBSERVER = 'observer'


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


HEADERS_TO_IGNORE = ['Content-Encoding', 'Content-Length', 'Transfer-Encoding', 'Trailer']
