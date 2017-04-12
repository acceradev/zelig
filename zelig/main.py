import logging
import sys

from zelig import config
from zelig.client import start_client
from zelig.constants import ZeligMode
from zelig.server import start_server

logger = logging.getLogger('zelig')
logger.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(logging.StreamHandler(sys.stdout))


def main():
    conf = config.get_config()
    logger.info('Start zelig in "{mode}" mode'.format(mode=conf.mode.value))
    if conf.mode == ZeligMode.CLIENT:
        # Run coroutine for 'client' mode
        start_client(conf)
    else:
        # Run server for 'server', 'observer' and 'proxy' modes
        start_server(conf)


if __name__ == '__main__':
    main()