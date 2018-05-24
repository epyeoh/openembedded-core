import os
#import json
#import subprocess
#import scriptpath
#scriptpath.add_bitbake_lib_path()
#scriptpath.add_oe_lib_path()
#from oeqa.utils.git import GitRepo, GitError
#from testresultlog.testresultlogconfigparser import TestResultLogConfigParser
from testresultlog.testresultgitstore import TestResultGitStore
from testresultlog.testlogparser import TestLogParser

class TestResultUpdator(object):

    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.base_path = self.script_path + '/../../..'

    def _get_testsuite_from_testcase(self, testcase):
        testsuite = testcase[0:testcase.rfind(".")]
        return testsuite

    def _get_testmodule_from_testsuite(self, testsuite):
        testmodule = testsuite[0:testsuite.find(".")]
        return testmodule

    def get_testsuite_testcase_dictionary(self, testcase_status_dict):
        testcase_list = testcase_status_dict.keys()
        testsuite_testcase_dict = {}
        for testcase in testcase_list:
            testsuite = self._get_testsuite_from_testcase(testcase)
            if testsuite in testsuite_testcase_dict:
                testsuite_testcase_dict[testsuite].append(testcase)
            else:
                testsuite_testcase_dict[testsuite] = [testcase]
        return testsuite_testcase_dict

    def get_testmodule_testsuite_dictionary(self, testsuite_testcase_dict):
        testsuite_list = testsuite_testcase_dict.keys()
        testmodule_testsuite_dict = {}
        for testsuite in testsuite_list:
            testmodule = self._get_testmodule_from_testsuite(testsuite)
            if testmodule in testmodule_testsuite_dict:
                testmodule_testsuite_dict[testmodule].append(testsuite)
            else:
                testmodule_testsuite_dict[testmodule] = [testsuite]
        return testmodule_testsuite_dict

    def _remove_testsuite_from_testcase(self, testcase, testsuite):
        testsuite = testsuite + '.'
        testcase_remove_testsuite = testcase.replace(testsuite, '')
        return testcase_remove_testsuite

    def get_testcase_failed_or_error_logs_dictionary(self, log_file, testcase_status_dict):
        testlogparser = TestLogParser()
        testcase_list = testcase_status_dict.keys()
        testcase_failed_or_error_logs_dict = {}
        for testcase in testcase_list:
            test_status = testcase_status_dict[testcase]
            if test_status == 'FAILED' or test_status == 'ERROR':
                testsuite = self._get_testsuite_from_testcase(testcase)
                testfunction = self._remove_testsuite_from_testcase(testcase, testsuite)
                logs = testlogparser.get_test_log(log_file, test_status, testfunction, testsuite)
                testcase_failed_or_error_logs_dict[testcase] = logs
        return testcase_failed_or_error_logs_dict

def main(args):
    testlogparser = TestLogParser()
    testcase_status_dict = testlogparser.get_test_status(args.log_file)
    print('DEGUG: testcase_status_dict: %s' % testcase_status_dict)

    testresultupdator = TestResultUpdator()
    testsuite_testcase_dict = testresultupdator.get_testsuite_testcase_dictionary(testcase_status_dict)
    print('DEGUG: testsuite_testcase_dict:')
    print(testsuite_testcase_dict)
    testmodule_testsuite_dict = testresultupdator.get_testmodule_testsuite_dictionary(testsuite_testcase_dict)
    print('DEGUG: testmodule_testsuite_dict:')
    print(testmodule_testsuite_dict)
    test_logs_dict = testresultupdator.get_testcase_failed_or_error_logs_dictionary(args.log_file, testcase_status_dict)
    print('DEGUG: test_logs:')
    print(test_logs_dict)

    env_list = args.environment_list.split(",")
    testresultstore = TestResultGitStore()
    testresultstore.update_test_result(args.git_repo, args.git_branch, args.component, env_list, testmodule_testsuite_dict, testsuite_testcase_dict, testcase_status_dict, test_logs_dict)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('update', help='Update test result status into the specified test result template',
                                         description='Update test result status from the test log into the specified test result template')
    parser_build.set_defaults(func=main)
    parser_build.add_argument('-l', '--log_file', required=True, help='Full path to the test log file to be used for test result update')
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be updated ,default will be /poky/test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be updated with test result')
    parser_build.add_argument('-c', '--component', required=True, help='Component to be selected from conf/testplan_component.conf for creation of test environments')
    parser_build.add_argument('-e', '--environment_list', required=True, help='List of environment to be used to perform update')