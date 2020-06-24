#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import datetime
import logging
import os
import re
import sys
from argparse import ArgumentParser
from collections import namedtuple
from string import Template

from log_parser import parse

# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


DEFAULT_CONFIG_PATH = './parser_conf.ini'

LOG_FORMAT = '$remote_addr $remote_user  $http_x_real_ip [$time_local] "$request" ' \
             '$status $body_bytes_sent "$http_referer" ' \
             '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" ' \
             '$request_time'

LOG_FILENAME_TEMPLATE = r'nginx\-access\-ui\.log\-([1-2]\d{3}[0-1]\d[0-3]\d)(\.gz)?$'
REPORT_TEMPLATE_NAME = "./report.html"

default_config = {
    'REPORT_SIZE': 1000,
    'LOG_DIR': './log/',
    'REPORT_DIR': './reports/',
    'MONITOR_LOG_FILE': None
}

MAX_ERROR_PERC = 20

FileInfo = namedtuple('FileInfo', 'file_path file_date')


def get_config_file_name():
    parser = ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)

    return parser.parse_args().config


def load_config(default_config, config_file_name):
    conf_parser = configparser.ConfigParser()
    conf_parser.optionxform = lambda option: option.upper()
    conf_parser.read(config_file_name, encoding='UTF-8')

    config = default_config.copy()
    config.update(dict(conf_parser.items('main')))

    if not config["REPORT_DIR"].endswith("/"):
        config["REPORT_DIR"] += "/"

    if not config["LOG_DIR"].endswith("/"):
        config["LOG_DIR"] += "/"

    return config


def config_logging(log_file):
    logging.basicConfig(filename=log_file, format='%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', level=logging.INFO)


def find_last_log(log_dir):
    last_file_name = ''
    last_date = datetime.datetime(2000, 1, 1, 0, 0, 0).date()

    for file_name in os.listdir(log_dir):
        match = re.match(LOG_FILENAME_TEMPLATE, file_name)
        if match:
            date_str = match.group(1)
            file_date = datetime.datetime.strptime(date_str, '%Y%m%d').date()

            if file_date > last_date:
                last_date = file_date
                last_file_name = file_name
    return FileInfo(file_path=last_file_name, file_date=last_date)


def report_file_exists(report_dir, report_file_name):
    for file_name in os.listdir(report_dir):
        if file_name == report_file_name:
            return True

    return False


def save_result(result_table, file_name):
    with open(REPORT_TEMPLATE_NAME, 'r') as f:
        template = Template(f.read())

    with open(file_name, encoding="UTF-8", mode='w+') as f:
        f.write(template.safe_substitute(table_json=result_table))

    logging.info('Result saved to {}'.format(file_name))


def main(config):
    parse_result = parse(LOG_FORMAT, int(config["REPORT_SIZE"]), config["LOG_DIR"] + file_info.file_path)

    if parse_result.error_lines_perc > MAX_ERROR_PERC:
        logging.error('Could not parse {}% of lines'.format(parse_result.error_lines_perc))
        sys.exit()

    save_result(parse_result.result_table, config["REPORT_DIR"] + result_file_name)


if __name__ == "__main__":
    config_file_name = get_config_file_name()
    if not os.path.exists(config_file_name):
        logging.error('Configuration file {} not exist'.format(config_file_name))
        sys.exit('Configuration file {} not exist'.format(config_file_name))

    try:
        config = load_config(default_config, config_file_name)
    except (configparser.NoOptionError, configparser.NoSectionError) as e:
        logging.error('Invalid configuration file format: {}'.format(e))
        sys.exit('Invalid configuration file format: {}'.format(e))

    config_logging(config["MONITOR_LOG_FILE"])

    file_info = find_last_log(config["LOG_DIR"])
    if not file_info.file_path:
        logging.info('There are not log files to process')
        sys.exit()

    if not os.path.exists(config["REPORT_DIR"]):
        os.makedirs(config["REPORT_DIR"])

    result_file_name = 'report-{}.html'.format(file_info.file_date.strftime('%Y.%m.%d'))
    if report_file_exists(config["REPORT_DIR"], result_file_name):
        logging.info("Report {} already exists".format(result_file_name))
        sys.exit()

    try:
        main(config)
    except Exception as e:
        logging.exception('Parsing was stopped. Error: {}'.format(e))
        sys.exit('Parsing was stopped. Error: {}'.format(e))
