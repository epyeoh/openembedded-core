from testresultlog.testmatrixjsonencoder import TestEnvMatrixJsonEncoder
import subprocess
import os
scripts_path = os.path.dirname(os.path.realpath(__file__))
import json

class TestPlanGitWriter(object):

    def _create_testsuite_testcase_list(self, test_moduleclass_list, test_moduleclass_func_dict):
        #print('DEBUG: creating testsuite testcase for testsuite list: %s' % testsuite_list)
        json_object = {'testsuite':[]}
        for testsuite in test_moduleclass_list:
            #print('DEBUG: creating testsuite: %s' % testsuite)
            testsuite_dict = {}
            testsuite_dict['testsuitename'] = testsuite
            testcase_list = test_moduleclass_func_dict[testsuite]
            #print('DEBUG: creating testcase list: %s' % testcase_list)
            testsuite_dict['testcase'] = self._create_testcase_list(testcase_list, testsuite)
            json_object['testsuite'].append(testsuite_dict)
        return json_object

    def _create_testcase_list(self, testcase_list, testsuite_name):
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
        testsuite_testcase_list = self._create_testsuite_testcase_list(test_moduleclass_list, test_moduleclass_func_dict)
        return json.dumps(testsuite_testcase_list, sort_keys=True, indent=4)

    def _write_testsuite_testcase_json_data_structure_to_file(self, file_path, file_content):
        with open(file_path, 'a') as the_file:
            the_file.write(file_content)

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo])

    def write_testplan_to_storage(self, top_workspace_dir, test_env_matrix, test_module_moduleclass_dict, test_moduleclass_function_dict):
        file_write_dir = os.path.join(top_workspace_dir, 'test-results-new')
        print('DEBUG: print generated module json structure')
        for module_key in sorted(list(test_module_moduleclass_dict.keys())):
            module_json_structure = self._generate_testsuite_testcase_json_data_structure(test_module_moduleclass_dict[module_key], test_moduleclass_function_dict)
            print('DEBUG: print generated module json structure for %s' % module_key)
            print(module_json_structure)
            file_name = 'testresult_%s.json' % module_key
            #path_to_write_file = os.path.join(scripts_path, 'test-results')
            file_path = os.path.join(file_write_dir, file_name)
            print('DEBUG: path to write file: %s' % file_path)
            self._write_testsuite_testcase_json_data_structure_to_file(file_path, module_json_structure)
        git_repo_dir = os.path.join(top_workspace_dir, 'test-results-new-repo')
        self._push_testsuite_testcase_json_file_to_git_repo(file_write_dir, git_repo_dir)
