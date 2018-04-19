import re

class TestLogParser(object):

    def get_test_status(self, log_file):
        regex = ".*RESULTS - (?P<case_name>.*) - Testcase (?P<case_id>\d+): (?P<status>PASSED|FAILED)$"
        regex_comp = re.compile(regex)
        results = {}
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                m = regex_comp.search(line)
                if m:
                    print(m.group('case_name') + ': ' +  m.group('status'))
                    results[m.group('case_name')] = m.group('status')
        return results

    def get_test_log(self, log_file, case_name):
        pass
