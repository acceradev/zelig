import os

from .errors import MissingValueError, InvalidValueError

notset = object()


class Property:
    def __init__(self, key, default=notset):
        self._key = key
        self._default = default
        self._value = notset

    def clean(self, value):
        return value

    @property
    def key(self):
        return self._key

    @property
    def default(self):
        return self._default

    def __get__(self, instance, owner):
        if self._value is notset:
            self._value = self.__get_value()
        return self._value

    def __get_value(self):
        self.__check_has_value()
        value = os.environ.get(self.key, default=self.default)
        return self.clean(value)

    def __check_has_value(self):
        if self.key not in os.environ and self.default is notset:
            error_msg = f'You should set \'{self.key}\' environment variable'
            raise MissingValueError(error_msg)


class IntProperty(Property):
    def clean(self, value):
        try:
            return int(value)
        except TypeError:
            raise InvalidValueError(f'Value of {self.key} param should be integer')


class EnumProperty(Property):
    def __init__(self, key, enum_class, default=notset):
        self.enum_class = enum_class
        super().__init__(key=key, default=default)

    def clean(self, value):
        try:
            return self.enum_class(value)
        except ValueError:
            possible_values = ', '.join((f'{c.value}' for c in self.enum_class))
            raise InvalidValueError(f'Value of {self.key} param should be one of [{possible_values}]')


class MultiEnumProperty(EnumProperty):
    def clean(self, value):
        res = []
        for v in value.split():
            res.append(super().clean(v))

        if not res:
            possible_values = ', '.join((f'{c.value}' for c in self.enum_class))
            raise InvalidValueError(
                f'Value of {self.key} param should be one or more (space separated) of [{possible_values}]')
        return res


class PathProperty(object):
    def __init__(self, path=notset):
        self._path = self.__get_value(path)

    def __get__(self, instance, owner):
        return self._path

    def __get_value(self, path):
        if os.path.isdir(path) and os.path.exists(path):
            return path
        raise MissingValueError(
            f'"{path}" is not an existing directory. Please map "{path}" to your local path')
