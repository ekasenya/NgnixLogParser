from datetime import datetime
import os
import random
import unittest
import uuid

from log_parser import calc_report_data
import main


class ConfigTests(unittest.TestCase):
    def test_read_config(self):
        self.assertTrue(os.path.exists(main.DEFAULT_CONFIG_PATH))
        config = main.load_config({}, main.DEFAULT_CONFIG_PATH)
        self.assertEqual(int(config["report_size"]), 1000)


class ReportFileExistsTest(unittest.TestCase):
    report_file_path = "./report_{}.html".format(datetime.now().strftime('%Y%m%d'))

    def setUp(self) -> None:
        with open(self.report_file_path, 'w+') as f:
            f.write('')

    def test_report_exists(self):
        self.assertTrue(main.report_file_exists(os.path.dirname(self.report_file_path),
                                                os.path.basename(self.report_file_path)))

    def tearDown(self) -> None:
        os.remove(self.report_file_path)


def gen_lines(num_lines):
    for i in range(num_lines):
        ip = ".".join([str(random.randint(1, 256)) for _ in range(4)])

        if i % 10 == 0:
            url = '/index.html'
        else:
            url = '/banner/{}'.format(uuid.uuid4().hex)

        b = random.randint(42, 10000)
        line = '{} -  - [{}] "GET {} HTTP/1.1" 200 {} "-" "-" "-" "-" "-" 0.{}\n'.format(
            ip, datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0300'), url, b, random.randint(100, 999))

        yield line


class LogParserTests(unittest.TestCase):
    log_file_name = 'log_test'

    def setUp(self) -> None:
        self.config = main.load_config({}, main.DEFAULT_CONFIG_PATH)
        self.full_log_file_path = os.path.join(self.config["log_dir"], self.log_file_name)
        with open(self.full_log_file_path, 'w+') as f:
            for line in gen_lines(100):
                f.write(line)

    def test_parse_log(self):

        result_list = calc_report_data(main.LOG_FORMAT, int(self.config["report_size"]),
                                       self.full_log_file_path,
                                       int(self.config["max_error_perc"]))
        self.assertEqual(len(result_list), 91)

    def tearDown(self) -> None:
        os.remove(self.full_log_file_path)


if __name__ == '__main__':
    unittest.main()
