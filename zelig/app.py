from aiohttp import web


class ZeligServerApplication(web.Application):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config

    @property
    def config(self):
        return self._config
