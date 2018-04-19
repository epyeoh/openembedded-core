import subprocess
import os
import json
import pathlib

class TestPlanGitWriter(object):

    def _create_testsuite_testcase_dict(self, test_moduleclass_list, test_moduleclass_func_dict):
        #print('DEBUG: creating testsuite testcase for testsuite list: %s' % testsuite_list)
        json_object = {'testsuite':{}}
        testsuite_dict = json_object['testsuite']
        for testsuite in sorted(test_moduleclass_list):
            testsuite_dict[testsuite] = {'testcase': {}}
            print('DEBUG: testsuite: %s' % testsuite)
            print('DEBUG: test_moduleclass_func_dict[testsuite]: %s' % test_moduleclass_func_dict[testsuite])
            testsuite_dict[testsuite]['testcase'] = self._create_testcase_dict(test_moduleclass_func_dict[testsuite], testsuite)
        return json_object

    def _create_testcase_dict(self, testcase_list, testsuite_name):
        testcase_dict = {}
        for testcase in sorted(testcase_list):
            testcase_key = '%s.%s' % (testsuite_name, testcase)
            testcase_dict[testcase_key] = {"testlog": "","testresult": ""}
        #print('DEBUG: testcase_dict: %s' % testcase_dict)
        return testcase_dict

    def _deprecated_create_testsuite_testcase_list(self, test_moduleclass_list, test_moduleclass_func_dict):
        #print('DEBUG: creating testsuite testcase for testsuite list: %s' % testsuite_list)
        json_object = {'testsuite':[]}
        for testsuite in test_moduleclass_list:
            #print('DEBUG: creating testsuite: %s' % testsuite)
            testsuite_dict = {}
            testsuite_dict['testsuitename'] = testsuite
            testcase_list = test_moduleclass_func_dict[testsuite]
            #print('DEBUG: creating testcase list: %s' % testcase_list)
            testsuite_dict['testcase'] = self._deprecated_create_testcase_list(testcase_list, testsuite)
            json_object['testsuite'].append(testsuite_dict)
        return json_object

    def _deprecated_create_testcase_list(self, testcase_list, testsuite_name):
        testcaselist = []
        for testcase in testcase_list:
            testcase_dict = {}
            testcase_dict['testcasename'] = '%s.%s' % (testsuite_name, testcase)
            testcase_dict['testresult'] = ""
            testcase_dict['testlog'] = ""
            #testcase_dict['testprocedures'] = ""
            testcaselist.append(testcase_dict)
        #print('DEBUG: testcase_list: %s' % testcaselist)
        return testcaselist

    def _generate_testsuite_testcase_json_data_structure(self, test_moduleclass_list, test_moduleclass_func_dict):
        #testsuite_testcase_list = self._create_testsuite_testcase_list(test_moduleclass_list, test_moduleclass_func_dict)
        testsuite_testcase_list = self._create_testsuite_testcase_dict(test_moduleclass_list, test_moduleclass_func_dict)
        return json.dumps(testsuite_testcase_list, sort_keys=True, indent=4)

    def _write_testsuite_testcase_json_data_structure_to_file(self, file_path, file_content):
        with open(file_path, 'w') as the_file:
            the_file.write(file_content)

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo, git_branch):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo, "-b", git_branch])

    def _create_file_directory_list_for_environment_matrix(self, target_dir, test_env_matrix):
        directory_list = []
        for env_str in test_env_matrix:
            env_list = env_str.split(',')
            path = target_dir
            for env in env_list:
                path = os.path.join(path, env)
            directory_list.append(path)
        return directory_list

    def write_testplan_to_storage(self, test_env_matrix, test_module_moduleclass_dict, test_moduleclass_function_dict, workspace_dir, folder_name, git_repo_dir, git_branch):
        project_dir = os.path.join(workspace_dir, folder_name)
        environment_dir_list = self._create_file_directory_list_for_environment_matrix(project_dir, test_env_matrix)
        if len(environment_dir_list) == 0:
            print('ERROR: environment_dir_list is empty: %s' % environment_dir_list)
        for env_dir in environment_dir_list:
            pathlib.Path(env_dir).mkdir(parents=True, exist_ok=True)
        print('DEBUG: print generated module json structure')
        for module_key in sorted(list(test_module_moduleclass_dict.keys())):
            module_json_structure = self._generate_testsuite_testcase_json_data_structure(test_module_moduleclass_dict[module_key], test_moduleclass_function_dict)
            print('DEBUG: print generated module json structure for %s' % module_key)
            print(module_json_structure)
            file_name = 'testresult_%s.json' % module_key
            for env_dir in environment_dir_list:
                file_path = os.path.join(env_dir, file_name)
                print('DEBUG: path to write file: %s' % file_path)
                self._write_testsuite_testcase_json_data_structure_to_file(file_path, module_json_structure)
        self._push_testsuite_testcase_json_file_to_git_repo(workspace_dir, git_repo_dir, git_branch)
