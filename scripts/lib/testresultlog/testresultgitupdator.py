import os
import json
import subprocess

class TestResultGitUpdator(object):

    def _get_test_module_name_from_test_function(self, test_function):
        test_module_name = test_function[0:test_function.find(".")]
        return test_module_name

    def _get_test_moduleclass_name_from_test_function(self, test_function):
        test_function_remove_module = test_function[test_function.find(".")+1:]
        test_moduleclass_name = test_function_remove_module[0:test_function_remove_module.find(".")]
        return test_moduleclass_name

    def _get_testmodule_testfunction_dictionary(self, test_function_status_dict):
        test_function_list = test_function_status_dict.keys()
        test_module_function_dict = {}
        for test_func in test_function_list:
            module_name = self._get_test_module_name_from_test_function(test_func)
            if module_name in test_module_function_dict:
                test_module_function_dict[module_name].append(test_func)
            else:
                test_module_function_dict[module_name] = [test_func]
        return test_module_function_dict

    def _load_test_module_file_with_json_into_dictionary(self, file):
        with open(file, "r") as f:
            return json.load(f)

    def _update_testresult_dictionary(self, testresult_dict, test_module, testmodule_testfunction_dict, test_function_status_dict):
        test_function_list = testmodule_testfunction_dict[test_module]
        for test_funtion in test_function_list:
            test_function_status = test_function_status_dict[test_funtion]
            test_moduleclass_name = self._get_test_moduleclass_name_from_test_function(test_funtion)
            test_module_moduleclass_name = '%s.%s' % (test_module, test_moduleclass_name)
            testresult_dict['testsuite'][test_module_moduleclass_name]['testcase'][test_funtion]['testresult'] = test_function_status

    def _write_testsuite_testcase_json_data_structure_to_file(self, file_path, file_content):
        with open(file_path, 'w') as the_file:
            the_file.write(file_content)

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo, git_branch):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo, "-b", git_branch])

    def update_test_result(self, work_dir, test_function_status_dict, git_dir, git_branch):
        testmodule_testfunction_dict = self._get_testmodule_testfunction_dictionary(test_function_status_dict)
        test_module_list = testmodule_testfunction_dict.keys()
        for test_module in test_module_list:
            test_module_file = os.path.join(work_dir, 'testresult_%s.json' % test_module)
            if os.path.exists(test_module_file):
                #print('Found file (%s)' % test_module_file)
                testresult_dict = self._load_test_module_file_with_json_into_dictionary(test_module_file)
                #print('Test Result Dictionary : %s' % testresult_dict)
                self._update_testresult_dictionary(testresult_dict, test_module, testmodule_testfunction_dict, test_function_status_dict)
                #print('Updated Test Result Dictionary : %s' % testresult_dict)
                self._write_testsuite_testcase_json_data_structure_to_file(test_module_file, json.dumps(testresult_dict, sort_keys=True, indent=4))

            else:
                print('Cannot find file (%s)' % test_module_file)
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)



