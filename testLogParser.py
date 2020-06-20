import datetime
import os
import random
import unittest
import uuid

import log_parser
import main


class ConfigTests(unittest.TestCase):
    def test_read_config(self):
        config = {}
        main.load_config(config)
        self.assertEqual(config["REPORT_SIZE"], 1000)


class ReportFileExistsTest(unittest.TestCase):
    report_file_path = "./report_{}.html".format(datetime.datetime.now().strftime('%Y%m%d'))

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
            ip, datetime.datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0300'), url, b, random.randint(100, 999))

        yield line


class LogParserTests(unittest.TestCase):
    log_file_name = './log_test'

    def setUp(self) -> None:
        with open(self.log_file_name, 'w+') as f:
            for line in gen_lines(100):
                f.write(line)

    def test_parse_log(self):
        config = {}
        main.load_config(config)
        parser = log_parser.LogParser(main.LOG_FORMAT, 10000)
        parser.parse(self.log_file_name)
        result_table = parser.get_result_table()
        self.assertEqual(len(result_table), 91)

    def tearDown(self) -> None:
        os.remove(self.log_file_name)


if __name__ == '__main__':
    unittest.main()
