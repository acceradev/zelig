import sys

from zelig import config
from zelig.client import start_playback
from zelig.config import ConfigurationError
from zelig.constants import ZeligMode
from zelig.server import start_server
from zelig.summary import print_summary
from zelig.log import logger


def start_zelig():
    try:
        conf = config.get_config()
    except ConfigurationError as e:
        logger.error(f'Configuration error - {e!s}')
        exit(1)

    logger.info('Start zelig in "{mode}" mode'.format(mode=conf.mode.value))
    if conf.mode == ZeligMode.PLAYBACK:
        # Run coroutine for 'playback' mode
        start_playback(conf)
    else:
        # Run server for 'serve', 'observe' and 'record' modes
        start_server(conf)


def main():
    arguments = sys.argv[1:]
    if not arguments:
        start_zelig()
    else:
        print_summary(arguments)

if __name__ == '__main__':
    main()
