import os
import unittest
from testresultlog.testresultlogconfigparser import TestResultLogConfigParser
from testresultlog.testplangitwriter import TestPlanGitWriter
import scriptpath
scriptpath.add_oe_lib_path()
scriptpath.add_bitbake_lib_path()

class TestPlanCreator(object):

    def _init_environment_multiplication_matrix(self, env_matrix, env_value_list, env):
        #print(env_value_list)
        for env_value in env_value_list:
            env_matrix.append('%s_%s' % (env, env_value))

    def _multiply_current_env_matrix_with_new_env_list(self, env_matrix, env_value_list, env):
        #print(env_value_list)
        ml = []
        for value in env_matrix:
            for new_value in env_value_list:
                ml.append('%s,%s' % (value, '%s_%s' % (env, new_value)))
        return ml

    def _generate_flat_list_of_test_module_function(self, test_suite):
        for test in test_suite:
            if unittest.suite._isnotsuite(test):
                yield test
            else:
                for subtest in self._generate_flat_list_of_test_module_function(test):
                    yield subtest

    def _get_test_moduleclass_name(self, test):
        test_module_name = test[test.find("(")+1:test.find(")")]
        #print('DEBUG: %s : module : %s' % (test, test_module_name))
        return test_module_name

    def _get_test_function_name(self, test):
        test_function_name = test[0:test.find("(")-1]
        #print('DEBUG: %s : function : %s' % (test, test_function_name))
        return test_function_name

    def _get_test_module_name_from_key(self, key):
        test_module_name = key[0:key.find(".")]
        return test_module_name

    def _get_test_class_name_from_key(self, key):
        test_class_name = key[key.find(".")+1:]
        return test_class_name

    def _get_test_configuration_list(self, conf_path, section):
        config_parser = TestResultLogConfigParser(conf_path)
        return config_parser.get_config_items(section)

    def _get_oeqa_source_dir(self, script_path, source):
        print('script_path: %s' % script_path)
        script_path = os.path.join(script_path, '..')
        if source == 'runtime':
            oeqa_dir = os.path.join(script_path, 'meta/lib/oeqa/runtime/cases')
        elif source == 'selftest':
            oeqa_dir = os.path.join(script_path, 'meta/lib/oeqa/selftest/cases')
        elif source == 'sdk':
            oeqa_dir = os.path.join(script_path, 'meta/lib/oeqa/sdk/cases')
        else:
            oeqa_dir = os.path.join(script_path, 'meta/lib/oeqa/sdkext/cases')
        return oeqa_dir

    def _get_test_module_and_test_function_list(self, test_dir):
        loader = unittest.TestLoader()
        test_suite = loader.discover(start_dir=test_dir, pattern='*.py')
        return self._generate_flat_list_of_test_module_function(test_suite)

    def get_test_environment_multiplication_matrix(self, test_component, component_conf, environment_conf):
        test_environment_list = self._get_test_configuration_list(component_conf, test_component)
        env_matrix = []
        for env in test_environment_list:
            env_value_list = self._get_test_configuration_list(environment_conf, env)
            if len(env_matrix) == 0:
                self._init_environment_multiplication_matrix(env_matrix, env_value_list, env)
            else:
                env_matrix = self._multiply_current_env_matrix_with_new_env_list(env_matrix, env_value_list, env)
        return env_matrix

    def get_test_moduleclass_test_function_dictionary(self, script_path, source):
        test_dir = self._get_oeqa_source_dir(script_path, source)
        print('test_dir: %s' % test_dir)
        test_module_function_list = self._get_test_module_and_test_function_list(test_dir)
        test_moduleclass_func_dict = {}
        for test in test_module_function_list:
            key = self._get_test_moduleclass_name(str(test))
            value = self._get_test_function_name(str(test))
            if key in test_moduleclass_func_dict:
                test_moduleclass_func_dict[key].append(value)
            else:
                test_moduleclass_func_dict[key] = [value]
        return test_moduleclass_func_dict

    def get_test_module_test_moduleclass_dictionary(self, test_moduleclass_func_dict):
        moduleclass_list = test_moduleclass_func_dict.keys()
        test_module_moduleclass_dict = {}
        for module_class in moduleclass_list:
            module_name = self._get_test_module_name_from_key(module_class)
            class_name = '%s.%s' % (module_name, self._get_test_class_name_from_key(module_class))
            if module_name in test_module_moduleclass_dict:
                test_module_moduleclass_dict[module_name].append(class_name)
            else:
                test_module_moduleclass_dict[module_name] = [class_name]
        return test_module_moduleclass_dict

def main(args):
    scripts_path = os.path.dirname(os.path.realpath(__file__))
    testplan_conf = os.path.join(scripts_path, 'conf/testplan.conf')
    component_conf = os.path.join(scripts_path, 'conf/testplan_component.conf')
    environment_conf = os.path.join(scripts_path, 'conf/testplan_component_environment.conf')

    testplan_creator = TestPlanCreator()
    test_env_matrix = testplan_creator.get_test_environment_multiplication_matrix(args.component, component_conf, environment_conf)
    print('DEGUG: test_env_matrix:')
    print(test_env_matrix)
    test_moduleclass_function_dict = testplan_creator.get_test_moduleclass_test_function_dictionary(args.script_path, args.source)
    print('DEGUG: test_moduleclass_function_dict:')
    print(test_moduleclass_function_dict)
    test_module_moduleclass_dict = testplan_creator.get_test_module_test_moduleclass_dictionary(test_moduleclass_function_dict)
    print('DEGUG: test_module_moduleclass_dict:')
    print(test_module_moduleclass_dict)

    testplan_git_writer = TestPlanGitWriter()
    testplan_git_writer.write_testplan_to_storage(test_env_matrix, test_module_moduleclass_dict, test_moduleclass_function_dict, args.component, args.script_path, args.git_repo, args.git_branch)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('create', help='Create testplan and test result template',
                                         description='Create the file structure representing testplan environments and its test result templates')
    parser_build.set_defaults(func=main)
    SOURCE = ('runtime', 'selftest', 'sdk', 'sdkext')
    parser_build.add_argument('-s', '--source', required=True, choices=SOURCE,
    help='Testcase source to be selected from the list (runtime, selftest, sdk or sdkext). '
         '"runtime" will search testcase available in poky/meta/lib/oeqa/runtime/cases. '
         '"selftest" will search testcase available in poky/meta/lib/oeqa/selftest/cases. '
         '"sdk" will search testcase available in poky/meta/lib/oeqa/sdk/cases. '
         '"sdkext" will search testcase available in poky/meta/lib/oeqa/sdkext/cases. ')
    parser_build.add_argument('-c', '--component', required=True, help='Component to be selected from conf/testplan_component.conf for creation of test environments')
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='Git repository to be created (optional, default will be /poky/test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be created for the git repository')
