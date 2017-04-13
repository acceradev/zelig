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


def check_errors(r1, r2):
    return r1['status'].get('error') or r2['status'].get('error')


def match_responses(r1, r2, match_on):
    if check_errors(r1, r2):
        # Force responses to not be equal on errors
        return False
    response_matchers = [getattr(ResponseMatchers, matcher) for matcher in match_on]
    matches = [m(r1, r2) for m in response_matchers]
    return all(matches)
