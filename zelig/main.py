import sys

from zelig import config
from zelig.client import start_playback
from zelig.config import ConfigurationError
from zelig.constants import ZeligMode, SUMMARY_ARGUMENT
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
    if SUMMARY_ARGUMENT in sys.argv:
        print_summary(sys.argv[1:])
    else:
        start_zelig()


if __name__ == '__main__':
    main()
