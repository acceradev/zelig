from zelig import config
from zelig.client import start_client
from zelig.config import ConfigurationError
from zelig.constants import ZeligMode
from zelig.server import start_server
from zelig.log import logger


def main():
    try:
        conf = config.get_config()
    except ConfigurationError as e:
        logger.error(f'Configuration error - {e!s}')
        exit(1)

    logger.info('Start zelig in "{mode}" mode'.format(mode=conf.mode.value))
    if conf.mode == ZeligMode.CLIENT:
        # Run coroutine for 'client' mode
        start_client(conf)
    else:
        # Run server for 'server', 'observer' and 'proxy' modes
        start_server(conf)


if __name__ == '__main__':
    main()
