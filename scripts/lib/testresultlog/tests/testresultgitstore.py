import unittest
import re
import json
import os
import sys
basepath = os.path.dirname(os.path.realpath(__file__)) + '/../../../..'
newpath = basepath + '/scripts/lib'
sys.path = sys.path + [newpath]
from testresultlog.testresultgitstore import TestResultGitStore

class TestResultGitStoreTest(unittest.TestCase):

    def test_testresultgitstore_can_create_project_environment_directory_path(self):
        gitstore = TestResultGitStore()
        project_dir = '/tmp/test-result-dir'
        test_environment_list = ['core-image-sato-sdk', 'minnowboard']
        project_env_dir = gitstore._create_project_environment_directory_path(project_dir, test_environment_list)
        print(project_env_dir)
        regex = '%s.core-image-sato-sdk.minnowboard' % project_dir
        regex_comp = re.compile(regex)
        m = regex_comp.search(project_env_dir)
        self.assertNotEqual(m, None)

    def test_testresultgitstore_can_create_project_environment_directory_path_without_environment(self):
        gitstore = TestResultGitStore()
        project_dir = '/tmp/test-result-dir'
        test_environment_list = []
        project_env_dir = gitstore._create_project_environment_directory_path(project_dir, test_environment_list)
        self.assertEqual(project_dir, project_env_dir)

    def test_testresultgitstore_can_create_testsuite_testcase_json_object(self):
        testsuite_list = ['dnf.DnfBasicTest', 'dnf.DnfRepoTest']
        testsuite_testcase_dict = {'dnf.DnfBasicTest': ['dnf.DnfBasicTest.test_dnf_help', 'dnf.DnfBasicTest.test_dnf_history'], 'dnf.DnfRepoTest': ['dnf.DnfRepoTest.test_dnf_install']}
        gitstore = TestResultGitStore()
        actual_test_json_data = gitstore._create_testsuite_testcase_json_object(testsuite_list, testsuite_testcase_dict)
        scripts_path = os.path.dirname(os.path.realpath(__file__))
        expected_test_json_data_file = os.path.join(scripts_path, 'testsuite_testcase_json_data.txt')
        with open(expected_test_json_data_file, "r") as f:
            expected_test_json_data = json.load(f)
        actual_testsuites_key = actual_test_json_data['testsuite'].keys()
        expected_testsuites_key = expected_test_json_data['testsuite'].keys()
        self.assertEqual(actual_testsuites_key, expected_testsuites_key)
        for testsuite_key in actual_testsuites_key:
            actual_testcase_keys = actual_test_json_data['testsuite'][testsuite_key]['testcase'].keys()
            expected_testcase_keys = expected_test_json_data['testsuite'][testsuite_key]['testcase'].keys()
            self.assertEqual(actual_testcase_keys, expected_testcase_keys)

    def test_testresultgitstore_can_create_test_result_for_runtime_project(self):
        git_dir = '/tmp/test-result-dir'
        git_branch = 'qa_2.5_m1_rc1'
        project  = 'runtime'
        environment_list = ['core-image-sato-sdk', 'minnowboard']
        testmodule_testsuite_dict = {'dnf': ['dnf.DnfRepoTest', 'dnf.DnfBasicTest']}
        testsuite_testcase_dict = {'dnf.DnfBasicTest': ['dnf.DnfBasicTest.test_dnf_help', 'dnf.DnfBasicTest.test_dnf_history'], 'dnf.DnfRepoTest': ['dnf.DnfRepoTest.test_dnf_install']}
        gitstore = TestResultGitStore()
        gitstore.create_test_result(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict)
        gitstore._checkout_git_repo(git_dir, git_branch)
        expected_git_file = os.path.join(git_dir, project)
        for env in environment_list:
            expected_git_file = os.path.join(expected_git_file, env)
        expected_git_file = os.path.join(expected_git_file, 'dnf.json')
        self.assertTrue(os.path.exists(expected_git_file))
        gitstore._remove_temporary_workspace_dir(git_dir)

    def test_testresultgitstore_can_load_test_module_file_with_valid_file_path(self):
        scripts_path = os.path.dirname(os.path.realpath(__file__))
        test_json_data_file = os.path.join(scripts_path, 'testsuite_testcase_json_data.txt')
        gitstore = TestResultGitStore()
        target_testresult_dict = gitstore._load_test_module_file_with_json_into_dictionary(test_json_data_file)
        self.assertNotEqual(target_testresult_dict, None)

    def test_testresultgitstore_can_load_test_module_file_with_invalid_file_path(self):
        scripts_path = os.path.dirname(os.path.realpath(__file__))
        test_json_data_file = os.path.join(scripts_path, 'testsuite_testcase_json_data_WRONG.txt')
        gitstore = TestResultGitStore()
        target_testresult_dict = gitstore._load_test_module_file_with_json_into_dictionary(test_json_data_file)
        self.assertEqual(target_testresult_dict, None)

    def test_testresultgitstore_can_update_target_testresult_dictionary_with_status(self):
        scripts_path = os.path.dirname(os.path.realpath(__file__))
        test_json_data_file = os.path.join(scripts_path, 'testsuite_testcase_json_data.txt')
        gitstore = TestResultGitStore()
        target_testresult_dict = gitstore._load_test_module_file_with_json_into_dictionary(test_json_data_file)
        self.assertNotEqual(target_testresult_dict, None)
        testsuite_list = ['dnf.DnfRepoTest', 'dnf.DnfBasicTest']
        testsuite_testcase_dict = {'dnf.DnfBasicTest': ['dnf.DnfBasicTest.test_dnf_help', 'dnf.DnfBasicTest.test_dnf_history'], 'dnf.DnfRepoTest': ['dnf.DnfRepoTest.test_dnf_install']}
        testcase_status_dict = {'dnf.DnfBasicTest.test_dnf_help': 'PASSED', 'dnf.DnfBasicTest.test_dnf_history': 'PASSED', 'dnf.DnfRepoTest.test_dnf_install': 'FAILED'}
        gitstore._update_target_testresult_dictionary_with_status(target_testresult_dict, testsuite_list, testsuite_testcase_dict, testcase_status_dict)
        for testsuite in testsuite_list:
            testcase_list = testsuite_testcase_dict[testsuite]
            for testcase in testcase_list:
                expected_test_status = testcase_status_dict[testcase]
                target_test_status = target_testresult_dict['testsuite'][testsuite]['testcase'][testcase]['testresult']
                self.assertEqual(expected_test_status, target_test_status)

    def test_testresultgitstore_can_update_test_result(self):
        git_dir = '/tmp/test-result-dir'
        git_branch = 'qa_2.5_m1_rc1'
        project  = 'runtime'
        environment_list = ['core-image-sato-sdk', 'minnowboard']
        testmodule_testsuite_dict = {'dnf': ['dnf.DnfRepoTest', 'dnf.DnfBasicTest']}
        testsuite_testcase_dict = {'dnf.DnfBasicTest': ['dnf.DnfBasicTest.test_dnf_help', 'dnf.DnfBasicTest.test_dnf_history'], 'dnf.DnfRepoTest': ['dnf.DnfRepoTest.test_dnf_install']}
        testcase_status_dict = {'dnf.DnfBasicTest.test_dnf_help': 'PASSED', 'dnf.DnfBasicTest.test_dnf_history': 'PASSED', 'dnf.DnfRepoTest.test_dnf_install': 'FAILED'}
        gitstore = TestResultGitStore()
        gitstore.create_test_result(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict)
        gitstore.update_test_result(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict, testcase_status_dict)
        gitstore._checkout_git_repo(git_dir, git_branch)
        test_json_data_file = os.path.join('/tmp/test-result-dir/runtime/core-image-sato-sdk/minnowboard', 'dnf.json')
        target_testresult_dict = gitstore._load_test_module_file_with_json_into_dictionary(test_json_data_file)
        target_failed_status = target_testresult_dict['testsuite']['dnf.DnfRepoTest']['testcase']['dnf.DnfRepoTest.test_dnf_install']['testresult']
        self.assertEqual(target_failed_status, 'FAILED')
        gitstore._remove_temporary_workspace_dir(git_dir)

if __name__ == '__main__':
    unittest.main()
