import os
import logging.config

__all__ = ['logger']

DEBUG = os.environ.get('DEBUG', '').lower() in ['true', '1']

CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(levelname)s] %(asctime)s %(name)s: %(message)s'
        },
        'zelig': {
            'format': '[%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'zelig': {
            'class': 'logging.StreamHandler',
            'formatter': 'zelig',
        },
    },
    'loggers': {
        'zelig': {
            'level': logging.DEBUG if DEBUG else logging.INFO,
            'handlers': ['zelig'],
            'propagate': False
        },
    },
    'root': {
        'handlers': ['default'],
        'level': logging.WARNING,
    },
}

logging.config.dictConfig(CONFIG)

logger = logging.getLogger('zelig')
