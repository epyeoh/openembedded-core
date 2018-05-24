import os
import unittest
from testresultlog.testresultlogconfigparser import TestResultLogConfigParser
from testresultlog.testresultgitstore import TestResultGitStore
import scriptpath
scriptpath.add_oe_lib_path()
scriptpath.add_bitbake_lib_path()

class TestPlanCreator(object):

    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.base_path = self.script_path + '/../../..'

    def _get_test_configuration_list(self, conf_path, section):
        config_parser = TestResultLogConfigParser(conf_path)
        return config_parser.get_config_items(section)

    def _init_environment_multiplication_matrix(self, env_matrix, new_env_list, new_env_header):
        #print(env_value_list)
        for env in new_env_list:
            env_matrix.append('%s_%s' % (new_env_header, env))

    def _multiply_current_env_list_with_new_env_list(self, cur_env_list, new_env_list, new_env_header):
        #print(env_value_list)
        multiplied_list = []
        for cur_env in cur_env_list:
            for new_env in new_env_list:
                multiplied_list.append('%s,%s' % (cur_env, '%s_%s' % (new_env_header, new_env)))
        return multiplied_list

    def get_test_environment_multiplication_matrix(self, test_component, component_conf, environment_conf):
        test_environment_list = self._get_test_configuration_list(component_conf, test_component)
        env_matrix = []
        for env in test_environment_list:
            env_value_list = self._get_test_configuration_list(environment_conf, env)
            if len(env_matrix) == 0:
                self._init_environment_multiplication_matrix(env_matrix, env_value_list, env)
            else:
                env_matrix = self._multiply_current_env_list_with_new_env_list(env_matrix, env_value_list, env)
        return env_matrix

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
    scripts_path = os.path.dirname(os.path.realpath(__file__))
    testplan_conf = os.path.join(scripts_path, 'conf/testplan.conf')
    component_conf = os.path.join(scripts_path, 'conf/testplan_component.conf')
    environment_conf = os.path.join(scripts_path, 'conf/testplan_component_environment.conf')

    testplan_creator = TestPlanCreator()
    test_env_matrix = testplan_creator.get_test_environment_multiplication_matrix(args.component, component_conf, environment_conf)
    print('DEGUG: test_env_matrix:')
    print(test_env_matrix)
    testsuite_testcase_dict = testplan_creator.get_testsuite_testcase_dictionary(args.source)
    print('DEGUG: testsuite_testcase_dict:')
    print(testsuite_testcase_dict)
    testmodule_testsuite_dict = testplan_creator.get_testmodule_testsuite_dictionary(testsuite_testcase_dict)
    print('DEGUG: testmodule_testsuite_dict:')
    print(testmodule_testsuite_dict)

    for env in test_env_matrix:
        env_list = env.split(",")
        print(env_list)
        testresultstore = TestResultGitStore()
        testresultstore.create_test_result(args.git_repo, args.git_branch, args.component, env_list, testmodule_testsuite_dict, testsuite_testcase_dict)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('create', help='Create testplan and test result template',
                                         description='Create the file structure representing testplan environments and its test result templates')
    parser_build.set_defaults(func=main)
    SOURCE = ('runtime', 'selftest', 'sdk', 'sdkext')
    parser_build.add_argument('-s', '--source', required=True, choices=SOURCE,
    help='Testcase source to be selected from the list (runtime, selftest, sdk or sdkext). '
         '"runtime" will search testcase available in meta/lib/oeqa/runtime/cases. '
         '"selftest" will search testcase available in meta/lib/oeqa/selftest/cases. '
         '"sdk" will search testcase available in meta/lib/oeqa/sdk/cases. '
         '"sdkext" will search testcase available in meta/lib/oeqa/sdkext/cases. ')
    parser_build.add_argument('-c', '--component', required=True, help='Component to be selected from conf/testplan_component.conf for creation of test environments')
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be created, default will be test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be created for the git repository')
