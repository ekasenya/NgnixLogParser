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
TIME_LIST = 'time_list'

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


def get_pattern(log_format):
    pattern_str = log_format

    pattern_str = pattern_str.replace('[', '\[')
    pattern_str = pattern_str.replace(']', '\]')
    pattern_str = pattern_str.replace('"', '\"')

    pattern_str = re.sub('|'.join(r'{}\b'.format(re.escape(s)) for s in pattern_dict),
                         lambda match: pattern_dict[match.group(0)], pattern_str)

    return re.compile(pattern_str)


def calc_report_data(log_format, file_path, max_error_perc, max_line_to_parse=0):
    error_lines_cnt = 0
    total_line_cnt = 0

    raw_result_dict = {}
    pattern = get_pattern(log_format)

    logging.info('Start parsing file {}'.format(file_path))
    for line_data in get_line_data(pattern, file_path):
        if not line_data.success:
            error_lines_cnt += 1
        total_line_cnt += 1
        if max_line_to_parse and (total_line_cnt >= max_line_to_parse):
            break

        if not line_data.url:
            continue

        add_line_data_to_dict(line_data, raw_result_dict)

    logging.info('Lines processed: {}. Lines parsed: {}. Line not parsed: {}'.format(
        total_line_cnt, total_line_cnt - error_lines_cnt, error_lines_cnt))

    error_lines_perc = round(error_lines_cnt / total_line_cnt * 100, 2)
    if error_lines_perc > max_error_perc:
        logging.error('Could not parse {}% of lines'.format(error_lines_perc))
        return []

    return raw_result_dict


def add_line_data_to_dict(line_data, result_dict):
    if line_data.url in result_dict:
        item = result_dict[line_data.url]
        item[COUNT] += 1
        item[TIME_SUM] += line_data.time
        if item[TIME_MAX] < line_data.time:
            item[TIME_MAX] = line_data.time
        item[TIME_LIST].append(line_data.time)
    else:
        result_dict[line_data.url] = {URL: line_data.url, COUNT: 1, TIME_SUM: line_data.time, TIME_MAX: line_data.time,
                                      TIME_LIST: [line_data.time]}


def get_line_data(pattern, file_path):
    open_file_func = gzip.open if file_path.endswith(".gz") else open
    with open_file_func(file_path, mode='rb') as f:
        while True:
            line = f.readline().decode('UTF-8')
            if not line:
                break

            yield parse_line(pattern, line)


def parse_line(pattern, line):
    url = ''
    time = 0

    result = pattern.match(line)

    if result:
        url = result.groupdict()['request'].split()[1]
        time = float(result.groupdict()['request_time'])

    return ParseLineResult(url, time, result is not None)


def prepare_data(result_dict, report_size):
    result_list = [value for value in result_dict.values()]

    total_count = sum([list_item[COUNT] for list_item in result_list])
    total_time = sum([list_item[TIME_SUM] for list_item in result_list])

    result_list.sort(key=lambda list_item: list_item[TIME_SUM], reverse=True)
    result_list = result_list[:report_size]

    for item in result_list:
        item[TIME_AVG] = round(item[TIME_SUM] / len(item[TIME_LIST]), 3)
        item[TIME_MEDIAN] = round(median(item[TIME_LIST]), 3)
        item[TIME_PERC] = round(item[TIME_SUM] / total_time * 100, 3)
        item[COUNT_PERC] = round(item[COUNT] / total_count * 100, 3)
        item[TIME_SUM] = round(item[TIME_SUM], 3)
        del(item[TIME_LIST])

    return result_list


def remove_time_list_from_dict(dictionary):
    del (dictionary[TIME_LIST])
    return dictionary
