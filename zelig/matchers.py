class ResponseMatchers:

    @staticmethod
    def status(r1, r2):
        return r1.get('status') == r2.get('status')

    @staticmethod
    def body(r1, r2):
        return r1.get('body') == r2.get('body')

    @staticmethod
    def headers(r1, r2):
        return r1.get('headers') == r2.get('headers')


def match_responses(r1, r2, match_on):
    try:
        response_matchers = [getattr(ResponseMatchers, matcher) for matcher in match_on]
    except AttributeError:
        # TODO: find a better way to handle this
        raise AttributeError('One of the specified matchers does not exist')
    matches = [m(r1, r2) for m in response_matchers]
    return all(matches)
