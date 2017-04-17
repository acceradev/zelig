import json
import os
import time

from vcr.serializers.compat import convert_to_unicode
from vcr.serializers.yamlserializer import serialize, extension

from zelig.constants import METADATA_FILE
from zelig.log import logger


def _write_to_file(path, data):
    dirname, filename = os.path.split(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, 'w') as f:
        f.write(data)


def _prepare_headers(data):
    data['headers'] = dict(((str(k), v) for k, v in data['headers'].items()))
    return data


def _prepare_request(request):
    request = _prepare_headers(request)
    request['body'] = request.pop('data')
    return request


def _prepare_report(data):
    data['request'] = convert_to_unicode(_prepare_request(data['request']))
    data['original_response'] = convert_to_unicode(data['original_response'])
    data['received_response'] = convert_to_unicode(_prepare_headers(data['received_response']))


def save_report(report_path, data, root_key='results'):
    _prepare_report(data)
    data = serialize({root_key: data})
    _write_to_file(report_path, data)


class Reporter:

    def __init__(self, directory, mode):
        self.directory = directory
        self.mode = mode
        self.reports_counter = 0
        self.total_played = 0
        self.started = None
        self.finished = None

    def __enter__(self):
        self.started = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        msg = f'Generated {self.reports_counter} reports.' + \
              (f' Look to {self.directory} for details' if self.reports_counter else '')
        logger.info(msg)

    def _update_requests_time(self):
        self.finished = time.time()

    def _save_report(self, report, index):
        report_path = os.path.join(self.directory, f'{index}{extension}')
        logger.debug(f'Saving report to {report_path}')
        save_report(report_path, report)

    def _update_meta(self):
        meta_path = os.path.join(self.directory, METADATA_FILE)
        data = {
            'reports_number': self.reports_counter,
            'started': self.started,
            'finished': self.finished,
            'total_played': self.total_played,
            'mode': self.mode.value
        }
        _write_to_file(meta_path, json.dumps(data))

    def record_metadata(self):
        self.total_played += 1

        self._update_requests_time()
        self._update_meta()

    def report(self, report, request_index=None):
        self.reports_counter += 1
        if not request_index:
            request_index = self.reports_counter
        self._save_report(report, request_index)
