# test case management tool - parse test result for OEQA automated tests
#
# Copyright (c) 2018, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
import re

class OeqaLogParser(object):

    def get_test_status(self, log_file):
        regex = ".*RESULTS - (?P<case_name>.*) - Testcase .*: (?P<status>PASSED|FAILED|SKIPPED|ERROR|UNKNOWN).*$"
        regex_comp = re.compile(regex)
        results = {}
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                m = regex_comp.search(line)
                if m:
                    results[m.group('case_name')] = m.group('status')
        return results

    def get_runtime_test_image_environment(self, log_file):
        regex = "core-image.*().*Ran.*tests in .*s"
        regex_comp = re.compile(regex)
        image_env = ''
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                m = regex_comp.search(line)
                if m:
                    image_env = line[:line.find("(")-1]
                    image_env = image_env.strip()
                    break
        return image_env

    def get_runtime_test_qemu_environment(self, log_file):
        regex = "DEBUG: launchcmd=runqemu*"
        regex_comp = re.compile(regex)
        qemu_env = ''
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                m = regex_comp.search(line)
                if m:
                    qemu_list = ['qemuarm', 'qemuarm64', 'qemumips', 'qemumips64', 'qemuppc', 'qemux86', 'qemux86-64']
                    for qemu in qemu_list:
                        if qemu in line:
                            qemu_env = qemu
                            break
        return qemu_env

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
                    return logs
                else:
                    state = self._search_log_to_capture(logs, line, state, regex_comp_start, regex_comp_end_fail_or, regex_comp_end_error_or, regex_comp_end)
