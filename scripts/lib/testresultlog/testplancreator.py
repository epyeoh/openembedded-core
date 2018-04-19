import os
import sys
import unittest
from testresultlog.testresultlogconfigparser import TestResultLogConfigParser

scripts_path = os.path.dirname(os.path.realpath(__file__))
lib_path = scripts_path + '/lib'
sys.path = sys.path + [lib_path]
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

    def get_test_moduleclass_test_function_dictionary(self, test_dir):
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
