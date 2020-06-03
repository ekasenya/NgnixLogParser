import file_info


class LogParser:

    def __init__(self, file_info):
        self.file_info = file_info

    def parser(self):
        for line in self.read_line():
            self.parse_line(line)

    def read_line(self):
        with open(self.file_info.file_path, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                yield line

    def parse_line(self, line):
        print(line)
