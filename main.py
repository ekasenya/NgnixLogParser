#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

from log_parser import LogParser
from string import Template
from collections import namedtuple
import os
import sys
import logging
import configparser
from argparse import ArgumentParser
import datetime
import re


DEFAULT_CONFIG_PATH = './parser_conf.ini'
CONFIG_SECTION_NAME = 'main'

LOG_FORMAT = '$remote_addr $remote_user  $http_x_real_ip [$time_local] "$request" ' \
             '$status $body_bytes_sent "$http_referer" ' \
             '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" ' \
             '$request_time'

LOG_FILENAME_TEMPLATE = r'nginx\-access\-ui\.log\-[1-2]\d{3}[0-1]\d[0-3]\d(\.gz)?$'
REPORT_TEMPLATE_NAME = "./report.html"

MAX_ERROR_PERC = 20

FileInfo = namedtuple('FileInfo', 'file_path file_date')


def get_config_file_name():
    parser = ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)

    return parser.parse_args().config


def load_config(config):
    try:
        conf_parser = configparser.ConfigParser()
        conf_parser.read(DEFAULT_CONFIG_PATH, encoding='UTF-8')

        if conf_parser.has_option(CONFIG_SECTION_NAME, 'report_size'):
            config['REPORT_SIZE'] = conf_parser.get(CONFIG_SECTION_NAME, 'report_size')
        else:
            config['REPORT_SIZE'] = 1000

        if conf_parser.has_option(CONFIG_SECTION_NAME, 'log_dir'):
            config['LOG_DIR'] = conf_parser.get(CONFIG_SECTION_NAME, 'log_dir')
        else:
            config['LOG_DIR'] = './log/'

        if conf_parser.has_option(CONFIG_SECTION_NAME, 'report_dir'):
            config['REPORT_DIR'] = conf_parser.get(CONFIG_SECTION_NAME, 'report_dir')
        else:
            config['REPORT_DIR'] = './reports/'

        if conf_parser.has_option(CONFIG_SECTION_NAME, 'monitor_log_file'):
            config['MONITOR_LOG_FILE'] = conf_parser.get(CONFIG_SECTION_NAME, 'monitor_log_file')
        else:
            config['MONITOR_LOG_FILE'] = None

        if not config["REPORT_DIR"].endswith("/"):
            config["REPORT_DIR"] += "/"

        if not config["LOG_DIR"].endswith("/"):
            config["LOG_DIR"] += "/"

        return True
    except (configparser.NoOptionError, configparser.NoSectionError):
        logging.error('Invalid config file format')
        return False


def config_logging(log_file):
    logging.basicConfig(filename=log_file, format='%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', level=logging.INFO)


def find_last_log(log_dir):
    last_file_name = ''
    last_date = datetime.datetime(2000, 1, 1, 0, 0, 0).date()

    for file_name in os.listdir(log_dir):
        if re.match(LOG_FILENAME_TEMPLATE, file_name):
            date_str = next(re.finditer(r'[1-2]\d{3}[0-1]\d[0-3]\d', file_name)).group(0)
            dt = datetime.datetime.strptime(date_str, '%Y%m%d').date()

            if (dt > last_date):
                last_date = dt
                last_file_name = file_name
    return FileInfo(file_path=last_file_name, file_date=last_date)


def report_file_exists(report_dir, report_file_name):
    for file_name in os.listdir(report_dir):
        if (file_name == report_file_name):
            return True

    return False


def save_result(result_table, file_name):
    with open(REPORT_TEMPLATE_NAME, 'r') as f:
        template = Template(f.read())

    with open(file_name, encoding="UTF-8", mode='w+') as f:
        f.write(template.safe_substitute(table_json=result_table))

    logging.info('Result saved to {}'.format(file_name))


def main():
    try:
        config = {}
        if not load_config(config):
            sys.exit()

        config_logging(config["MONITOR_LOG_FILE"])

        file_info = find_last_log(config["LOG_DIR"])
        if (file_info.file_path == ''):
            logging.info('There are not log files to process')
            sys.exit()

        if not os.path.exists(config["REPORT_DIR"]):
            os.makedirs(config["REPORT_DIR"])

        result_file_name = 'report-{}.html'.format(file_info.file_date.strftime('%Y.%m.%d'))
        if report_file_exists(config["REPORT_DIR"], result_file_name):
            logging.info("Report {} already exists".format(result_file_name))
            sys.exit()

        log_parser = LogParser(LOG_FORMAT)
        log_parser.parse(config["LOG_DIR"] + file_info.file_path)

        if (log_parser.get_error_line_perc() > MAX_ERROR_PERC):
            logging.error('Could not parse {}% of lines'.format(log_parser.error_lines_perc))
            sys.exit()

        save_result(log_parser.get_result_table(), config["REPORT_DIR"] + result_file_name)
    except Exception as e:
        logging.exception('Parsing was stopped. Error: {}'.format(e))


if __name__ == "__main__":
    main()
