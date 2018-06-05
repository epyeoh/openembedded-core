import os
import unittest

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

    def _get_oeqa_source_dir(self, source):
        if source == 'runtime':
            oeqa_dir = os.path.join(self.base_path, 'meta/lib/oeqa/runtime/cases')
        elif source == 'selftest':
            oeqa_dir = os.path.join(self.base_path, 'meta/lib/oeqa/selftest/cases')
        elif source == 'sdk':
            oeqa_dir = os.path.join(self.base_path, 'meta/lib/oeqa/sdk/cases')
        else:
            oeqa_dir = os.path.join(self.base_path, 'meta/lib/oeqa/sdkext/cases')
        return oeqa_dir

    def _discover_unittest_testsuite_testcase(self, test_dir):
        loader = unittest.TestLoader()
        testsuite_testcase = loader.discover(start_dir=test_dir, pattern='*.py')
        return testsuite_testcase

    def _generate_flat_list_of_unittest_testcase(self, testsuite):
        for test in testsuite:
            if unittest.suite._isnotsuite(test):
                yield test
            else:
                for subtest in self._generate_flat_list_of_unittest_testcase(test):
                    yield subtest

    def _get_testsuite_from_unittest_testcase(self, unittest_testcase):
        testsuite = unittest_testcase[unittest_testcase.find("(")+1:unittest_testcase.find(")")]
        #print('DEBUG: %s : testsuite : %s' % (unittest_testcase, testsuite))
        return testsuite

    def _get_testcase_from_unittest_testcase(self, unittest_testcase):
        testcase = unittest_testcase[0:unittest_testcase.find("(")-1]
        testsuite = self._get_testsuite_from_unittest_testcase(unittest_testcase)
        testcase = '%s.%s' % (testsuite, testcase)
        #print('DEBUG: %s : testcase : %s' % (unittest_testcase, testcase))
        return testcase

    def _get_testmodule_from_testsuite(self, testsuite):
        testmodule = testsuite[0:testsuite.find(".")]
        return testmodule

    def get_testsuite_testcase_dictionary(self, source):
        work_dir = self._get_oeqa_source_dir(source)
        print('work_dir: %s' % work_dir)
        unittest_testsuite_testcase = self._discover_unittest_testsuite_testcase(work_dir)
        unittest_testcase_list = self._generate_flat_list_of_unittest_testcase(unittest_testsuite_testcase)
        testsuite_testcase_dict = {}
        for unittest_testcase in unittest_testcase_list:
            testsuite = self._get_testsuite_from_unittest_testcase(str(unittest_testcase))
            testcase = self._get_testcase_from_unittest_testcase(str(unittest_testcase))
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

def main(args):
    testlogparser = TestLogParser()
    testcase_status_dict = testlogparser.get_test_status(args.log_file)
    print('DEGUG: testcase_status_dict: %s' % testcase_status_dict)
    if args.source == 'runtime':
        runtime_image_env = testlogparser.get_runtime_test_image_environment(args.log_file)
        print('runtime image environment: %s' % runtime_image_env)

    testresultupdator = TestResultUpdator()
    testsuite_testcase_dict = testresultupdator.get_testsuite_testcase_dictionary(args.source)
    print('DEGUG: testsuite_testcase_dict:')
    print(testsuite_testcase_dict)
    testmodule_testsuite_dict = testresultupdator.get_testmodule_testsuite_dictionary(testsuite_testcase_dict)
    print('DEGUG: testmodule_testsuite_dict:')
    print(testmodule_testsuite_dict)

    test_logs_dict = testresultupdator.get_testcase_failed_or_error_logs_dictionary(args.log_file, testcase_status_dict)
    print('DEGUG: test_logs:')
    print(test_logs_dict)

    if runtime_image_env not in args.environment_list:
        args.environment_list = '%s,%s' % (runtime_image_env, args.environment_list)
    env_list = args.environment_list.split(",")
    testresultstore = TestResultGitStore()
    testresultstore.smart_update_test_result(args.git_repo, args.git_branch, args.component, env_list, testmodule_testsuite_dict, testsuite_testcase_dict, testcase_status_dict, test_logs_dict)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('smartupdate', help='Smart update test result status into the specified test result template',
                                         description='Update test result status from the test log into the specified test result template')
    parser_build.set_defaults(func=main)
    parser_build.add_argument('-l', '--log_file', required=True, help='Full path to the test log file to be used for test result update')
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be updated ,default will be /poky/test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be updated with test result')
    SOURCE = ('runtime', 'selftest', 'sdk', 'sdkext')
    parser_build.add_argument('-s', '--source', required=True, choices=SOURCE,
    help='Testcase source to be selected from the list (runtime, selftest, sdk or sdkext). '
         '"runtime" will search testcase available in meta/lib/oeqa/runtime/cases. '
         '"selftest" will search testcase available in meta/lib/oeqa/selftest/cases. '
         '"sdk" will search testcase available in meta/lib/oeqa/sdk/cases. '
         '"sdkext" will search testcase available in meta/lib/oeqa/sdkext/cases. ')
    parser_build.add_argument('-c', '--component', required=True, help='Component selected (as the top folder) to store the related test environments')
    parser_build.add_argument('-e', '--environment_list', required=True, help='List of environment to be used to perform update')