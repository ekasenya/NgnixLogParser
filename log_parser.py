# -*- coding: utf-8 -*-

import gzip
import logging
import re
from collections import namedtuple
from statistics import median

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

ParseLineResult = namedtuple('ParseLineResult', 'url time success')
ParseResult = namedtuple('ParseResult', 'result_table error_lines_perc')


def get_pattern(log_format):
    pattern_str = log_format

    pattern_str = pattern_str.replace('[', '\[')
    pattern_str = pattern_str.replace(']', '\]')
    pattern_str = pattern_str.replace('"', '\"')

    pattern_str = re.sub('|'.join(r'{}\b'.format(re.escape(s)) for s in pattern_dict),
                         lambda match: pattern_dict[match.group(0)], pattern_str)

    return re.compile(pattern_str)


def parse(log_format, report_size, file_path, max_line_to_parse):
    file_path = file_path

    error_lines_cnt = 0
    total_line_cnt = 0

    result_table = []
    url_times = {}
    pattern = get_pattern(log_format)
    group_name_by_index = dict([(v, k) for k, v in pattern.groupindex.items()])

    logging.info('Start parsing file {}'.format(file_path))
    for tup in parse_line(pattern, group_name_by_index, file_path, max_line_to_parse):
        if not tup.success:
            error_lines_cnt += 1
        total_line_cnt += 1

        if tup.url == '':
            continue

        item = next((elem for elem in result_table if elem[URL] == tup.url), None)

        if item is None:
            result_table.append({URL: tup.url, COUNT: 1, TIME_SUM: tup.time, TIME_MAX: tup.time})
        else:
            item[COUNT] += 1
            item[TIME_SUM] += tup.time
            if item[TIME_MAX] < tup.time:
                item[TIME_MAX] = tup.time

        if tup.url in url_times:
            url_times[tup.url].append(tup.time)
        else:
            url_times[tup.url] = [tup.time]

    prepare_data(result_table, report_size, url_times)

    logging.info('Lines processed: {}. Lines parsed: {}. Line not parsed: {}'.format(
        total_line_cnt, total_line_cnt - error_lines_cnt, error_lines_cnt))

    return ParseResult(result_table,  round(error_lines_cnt / total_line_cnt * 100, 2))


def parse_line(pattern, group_name_by_index, file_path, max_line_to_parse):
    cnt = 0
    is_gz = file_path.endswith(".gz")
    with gzip.open(file_path, mode='rb') if is_gz else open(file_path, encoding="UTF-8", mode='r') as f:
        while True:
            cnt += 1
            if (max_line_to_parse > 0) & (cnt > max_line_to_parse):
                break

            line = f.readline().decode('UTF-8') if is_gz else f.readline()
            if not line:
                break

            match_count = 0

            url = ''
            time = 0

            result = pattern.finditer(line)
            for match in result:
                match_count += 1
                for group_index, value in enumerate(match.groups()):
                    if (value is not None) & ((group_index + 1) in group_name_by_index):
                        if group_name_by_index[group_index + 1] == 'request':
                            url = re.split(r' ', value)[1]
                        elif group_name_by_index[group_index + 1] == 'request_time':
                            time = round(float(value), 3)

            yield ParseLineResult(url, time, match_count != 0)


def prepare_data(result_table, report_size, url_times):
    result_table.sort(key=lambda item: item[TIME_SUM], reverse=True)
    result_table = result_table[:report_size]

    total_count = sum(map(lambda item: item[COUNT], result_table))
    total_time = sum(map(lambda item: item[TIME_SUM], result_table))

    for item in result_table:
        item[TIME_AVG] = round(item[TIME_MAX] / len(result_table), 3)
        item[TIME_MEDIAN] = round(median(url_times[item[URL]]), 3) if item[URL] in url_times else 0
        item[TIME_PERC] = round(item[TIME_SUM] / total_time, 3)
        item[COUNT_PERC] = round(item[COUNT] / total_count * 100, 3)
        item[TIME_SUM] = round(item[TIME_SUM], 3)
