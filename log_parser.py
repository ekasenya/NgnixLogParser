# -*- coding: utf-8 -*-

import file_info
from statistics import median
import re

URL = 'url'
COUNT = 'count'
COUNT_PROC = 'count_perc'
TIME_SUM = 'time_sum'
TIME_AVG = 'time_avg'
TIME_PERC = 'time_perc'
TIME_MAX = 'time_max'
TIME_MEDIAN = 'time_med'

pattern_dict = {
    '$remote_addr': r'(?P<remote_addr>\d+.\d+.\d+.\d+)',
    '$remote_user': r'(?P<remote_user>(\w)+|\-)',
    '$http_x_real_ip': r'(?P<http_x_real_ip>\d+.\d+.\d+.\d+|\-)',
    '$time_local': r'(?P<time_local>[0-3][0-9]/[A-Za-z]{3}/[0-9]{4}:[0-9]{2}:[0-5][0-9]:[0-5][0-9] [-+0-9]+)',
    '$request': r'(?P<request>[A-Z]+ [\d\D]+ HTTP/[0-9.]+)',
    '$status': r'(?P<status>\d+)',
    '$body_bytes_sent': r'(?P<body_bytes_sent>\d+)',
    '$http_referer': r'(?P<http_referer>[\d\D]+|\-)',
    '$http_user_agent': r'(?P<http_user_agent>[\d\D]+|\-)',
    '$http_x_forwarded_for': r'(?P<http_x_forwarded_for>\d+.\d+.\d+.\d+|\-)',
    '$http_X_REQUEST_ID': r'(?P<http_X_REQUEST_ID>\d+-\d+-\d+-\d+|\-)',
    '$http_X_RB_USER': r'(?P<http_X_RB_USER>\w+|\-)',
    '$request_time': r'(?P<request_time>\d+.\d{3})'
    }


class LogParser:
    result_table = []
    url_times = {}
    pattern = None

    def __init__(self, file_info, log_format):
        self.file_info = file_info
        self.log_format = log_format

    def get_pattern(self):
        if (self.pattern is None):
            pattern_str = self.log_format

            pattern_str = pattern_str.replace('[', '\[')
            pattern_str = pattern_str.replace(']', '\]')
            pattern_str = pattern_str.replace('"', '\"')

            pattern_str = re.sub('|'.join(r'{}\b'.format(re.escape(s)) for s in pattern_dict),
                                 lambda match: pattern_dict[match.group(0)], pattern_str)
            self.pattern = re.compile(pattern_str)
        return self.pattern

    def parse(self):
        for line in self.read_line():
            self.parse_line(line)
        self.prepare_data()

    def read_line(self):
        with open(self.file_info.file_path, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                yield line

    def parse_line(self, line):
        p = self.get_pattern()
        result = p.finditer(line)
        group_name_by_index = dict([(v, k) for k, v in p.groupindex.items()])

        match_count = 0
        url = ''
        time = 0
        for match in result:
            match_count += 1
            for group_index, value in enumerate(match.groups()):
                if ( (not value is None) & ((group_index + 1) in group_name_by_index)):
                    if (group_name_by_index[group_index + 1] == 'url'):
                        url = value
                    elif (group_name_by_index[group_index + 1] == 'request_time'):
                        time = float(value)

        if (match_count == 0):
            print('line format is wrong \n', line)

        item = next((elem for elem in self.result_table if elem[URL] == url), None)

        if (item is None):
            self.result_table.append({URL: url, COUNT: 1, TIME_SUM: time, TIME_MAX: time})
        else:
            item[COUNT] += 1
            item[TIME_SUM] += time
            if (item[TIME_MAX] < time):
                item[TIME_MAX] = time

        if (url in self.url_times):
            self.url_times[url].append(time)
        else:
            self.url_times[url] = [time]

    def prepare_data(self):
        for item in self.result_table:
            item[TIME_AVG] = item[TIME_MAX] / len(self.result_table)
            item[TIME_MEDIAN] = median(self.url_times[item[URL]]) if item[URL] in self.url_times else 0

    def get_result_table(self):
        return self.result_table
