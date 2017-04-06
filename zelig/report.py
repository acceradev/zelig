import logging
import os

from vcr.serializers.compat import convert_to_unicode
from vcr.serializers.yamlserializer import serialize


logger = logging.getLogger('zelig')


def _write_to_file(path, data):
    logger.info('Saving report to {path}'.format(path=path))
    dirname, filename = os.path.split(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'w') as f:
        f.write(data)


def create_report(report_path, matches):
    for match in matches:
        match['original_response'] = convert_to_unicode(match['original_response'])
        match['received_response'] = convert_to_unicode(match['received_response'])
    data = serialize({'matches': matches})
    _write_to_file(report_path, data)

