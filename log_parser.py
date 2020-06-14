# -*- coding: utf-8 -*-

from statistics import median
import re
import logging
import gzip

URL = 'url'
COUNT = 'count'
COUNT_PERC = 'count_perc'
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
    '$request_time': r'(?P<request_time>\d+.\d+)'
}


class LogParser:
    result_table = []
    url_times = {}
    pattern = None

    error_lines_cnt = 0
    total_line_cnt = 0
    error_lines_perc = 0

    def __init__(self, log_format):
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

    def parse(self, file_path):
        self.file_path = file_path
        self.error_lines_cnt = 0
        self.total_line_cnt = 0
        self.error_lines_perc = 0

        logging.info('Start parsing file {}'.format(file_path))

        for tup in self.parse_line():
            if (tup[0] == ''):
                continue

            url = tup[0]
            time = tup[1]
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

        self.prepare_data()

    def parse_line(self):
        p = self.get_pattern()
        group_name_by_index = dict([(v, k) for k, v in p.groupindex.items()])

        cnt = 0
        is_gz = self.file_path.endswith(".gz")
        with gzip.open(self.file_path, mode='r') if is_gz else open(self.file_path, encoding="UTF-8", mode='r')  as f:
            while True:
                cnt += 1
                if cnt > 20000:
                    break

                line = f.readline().decode('UTF-8') if is_gz else f.readline()
                if not line:
                    break

                match_count = 0

                url = ''
                time = 0

                result = p.finditer(line)
                for match in result:
                    match_count += 1
                    for group_index, value in enumerate(match.groups()):
                        if ((value is not None) & ((group_index + 1) in group_name_by_index)):
                            if (group_name_by_index[group_index + 1] == 'request'):
                                url = re.split(r' ', value)[1]
                            elif (group_name_by_index[group_index + 1] == 'request_time'):
                                time = round(float(value), 3)

                if (match_count == 0):
                    self.error_lines_cnt += 1
                self.total_line_cnt += 1

                yield (url, time)

    def prepare_data(self):
        self.result_table.sort(key=lambda item: item[TIME_SUM], reverse=True)
        total_count = sum(map(lambda item: item[COUNT], self.result_table))
        total_time = sum(map(lambda item: item[TIME_SUM], self.result_table))
        print('total_count = {}'.format(total_count))
        print('total_time = {}'.format(total_time))

        self.result_table = self.result_table[:1000]

        total_count = sum(map(lambda item: item[COUNT], self.result_table))
        total_time = sum(map(lambda item: item[TIME_SUM], self.result_table))

        print(self.result_table)

        print('total_count = {}'.format(total_count))
        print('total_time = {}'.format(total_time))

        for item in self.result_table:
            item[TIME_AVG] = round(item[TIME_MAX] / len(self.result_table), 3)
            item[TIME_MEDIAN] = round(median(self.url_times[item[URL]]), 3) if item[URL] in self.url_times else 0
            item[TIME_PERC] = round(item[TIME_SUM] / total_time, 3)
            item[COUNT_PERC] = round(item[COUNT] / total_count * 100, 3)
            item[TIME_SUM] = round(item[TIME_SUM], 3)

        self.error_lines_perc = round(self.error_lines_cnt / self.total_line_cnt * 100, 2)

        logging.info('Lines processed: {}. Lines parsed: {}. Line not parsed: {}'.format(self.total_line_cnt, self.total_line_cnt - self.error_lines_cnt, self.error_lines_cnt))

    def get_result_table(self):
        return self.result_table

    def get_error_line_perc(self):
        return self.error_lines_perc
