from vcr.request import Request


class ExtendedRequest(Request):
    def __init__(self, offset=0, **kwargs):
        super().__init__(**kwargs)
        self.offset = offset

    def _to_dict(self):
        return {
            'method': self.method,
            'uri': self.uri,
            'body': self.body,
            'offset': self.offset,
            'headers': dict(((k, [v]) for k, v in self.headers.items())),
        }

    @classmethod
    def _from_dict(cls, dct):
        return cls(**dct)


def monkey_patch():
    initial_from_dict = Request._from_dict
    initial_to_dict = Request._to_dict

    def patch():
        # For now we monkey patch default Request
        # cause we need it to support offset
        Request._from_dict = ExtendedRequest._from_dict
        Request._to_dict = ExtendedRequest._to_dict

    def restore():
        Request._from_dict = initial_from_dict
        Request._to_dict = initial_to_dict

    return patch, restore
