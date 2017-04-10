import logging
import os

from vcr.serializers.compat import convert_to_unicode
from vcr.serializers.yamlserializer import serialize

from matchers import match_responses


logger = logging.getLogger('zelig')


def _write_to_file(path, data):
    logger.info('Saving report to {path}'.format(path=path))
    dirname, filename = os.path.split(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'w') as f:
        f.write(data)


def _prepare_request(request):
    return {
        'body': request['data'],
        'headers': dict(((k, [v]) for k, v in request['headers'].items())),
        'method': request['method'],
        'url': request['url']
    }


def _prepare_report(data):
    for item in data:
        item['request'] = convert_to_unicode(_prepare_request(item['request']))
        item['original_response'] = convert_to_unicode(item['original_response'])
        item['received_response'] = convert_to_unicode(item['received_response'])


def save_report(report_path, data, root_key='results'):
    _prepare_report(data)
    data = serialize({root_key: data})
    _write_to_file(report_path, data)
