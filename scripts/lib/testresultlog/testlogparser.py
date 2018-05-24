import re

class TestLogParser(object):

    def get_test_status(self, log_file):
        regex = ".*RESULTS - (?P<case_name>.*) - Testcase (?P<case_id>\d+): (?P<status>PASSED|FAILED|SKIPPED|ERROR)$"
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

    def get_failed_tests(self, log_file):
        regex = ".*RESULTS - (?P<case_name>.*) - Testcase (?P<case_id>\d+): (?P<status>FAILED)$"
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

    def _search_log_to_capture(self, logs, line, state, regex_comp_start, regex_comp_end_fail_or, regex_comp_end_error_or, regex_comp_end):
        if state == 'Searching':
            m = regex_comp_start.search(line)
            if m:
                logs.append(line)
                return 'Found'
            else:
                return 'Searching'
        elif state == 'Found':
            m_fail = regex_comp_end_fail_or.search(line)
            m_error = regex_comp_end_error_or.search(line)
            m_end = regex_comp_end.search(line)
            if m_fail or m_error or m_end:
                return 'End'
            else:
                logs.append(line)
                return 'Found'

    def get_test_log(self, log_file, test_status, testcase_name, testsuite_name):
        if test_status == 'FAILED':
            test_status = 'FAIL'
        regex_search_start = ".*%s: %s \(%s\).*" % (test_status, testcase_name, testsuite_name)
        regex_search_end_fail_or = ".*FAIL: test.*"
        regex_search_end_error_or = ".*ERROR: test.*"
        regex_search_end = ".*Ran.*tests in .*s"
        regex_comp_start = re.compile(regex_search_start)
        regex_comp_end_fail_or = re.compile(regex_search_end_fail_or)
        regex_comp_end_error_or = re.compile(regex_search_end_error_or)
        regex_comp_end = re.compile(regex_search_end)
        state = 'Searching'
        logs = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if state == 'End':
                    #print(results)
                    return logs
                else:
                    state = self._search_log_to_capture(logs, line, state, regex_comp_start, regex_comp_end_fail_or, regex_comp_end_error_or, regex_comp_end)

