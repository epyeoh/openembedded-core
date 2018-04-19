import os
import sys

scripts_path = os.path.dirname(os.path.realpath(__file__))
lib_path = scripts_path + '/lib'
sys.path = sys.path + [lib_path]

from testresultlog.testresultgitupdator import TestResultGitUpdator
from testresultlog.testlogparser import TestLogParser
from testresultlog.testresultlogconfigparser import TestResultLogConfigParser

def main():

    testplan_conf = os.path.join(scripts_path, 'lib/testresultlog/conf/testplan.conf')

    configparser = TestResultLogConfigParser(testplan_conf)
    result_log_dir = configparser.get_testopia_config('TestResultUpdate', 'result_log_dir')
    work_dir = configparser.get_testopia_config('TestResultUpdate', 'work_dir')
    git_dir = configparser.get_testopia_config('TestResultUpdate', 'git_dir')
    testplan_cycle = configparser.get_testopia_config('TestResultUpdate', 'testplan_cycle')

    testlogparser = TestLogParser()
    test_function_status_dict = testlogparser.get_test_status(result_log_dir)
    print('DEGUG: test_function_status_dict: %s' % test_function_status_dict)
    testresultupdator = TestResultGitUpdator()
    testresultupdator.update_test_result(work_dir, test_function_status_dict, git_dir, testplan_cycle)

if __name__ == "__main__":
    sys.exit(main())
