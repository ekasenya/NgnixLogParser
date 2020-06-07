import file_info
from statistics import median

URL = 'url'
COUNT = 'count'
COUNT_PROC = 'count_perc'
TIME_SUM = 'time_sum'
TIME_AVG = 'time_avg'
TIME_PERC = 'time_perc'
TIME_MAX = 'time_max'
TIME_MEDIAN = 'time_med'


class LogParser:
    result_table = []
    url_times = {}

    def __init__(self, file_info):
        self.file_info = file_info

    def parser(self):
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
        url = 'all_urls'
        time = 0

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
