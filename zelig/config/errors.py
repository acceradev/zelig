class ConfigurationError(Exception):
    pass


class MissingValueError(ConfigurationError):
    pass


class InvalidValueError(ConfigurationError):
    pass