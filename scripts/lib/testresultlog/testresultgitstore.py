import tempfile
import os
import pathlib
import json
import subprocess
import scriptpath
scriptpath.add_bitbake_lib_path()
scriptpath.add_oe_lib_path()
from oeqa.utils.git import GitRepo, GitError

class TestResultGitStore(object):

    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.base_path = self.script_path + '/../../..'

    def _create_temporary_workspace_dir(self):
        return tempfile.mkdtemp(prefix='testresultlog.')

    def _create_project_environment_directory_path(self, project_dir, test_environment_list):
        project_env_dir = project_dir
        for env in test_environment_list:
            project_env_dir = os.path.join(project_env_dir, env)
        return project_env_dir

    def _get_testmodule_list(self, testmodule_testsuite_dict):
        return sorted(list(testmodule_testsuite_dict.keys()))

    def _create_testsuite_testcase_json_object(self, testsuite_list, testsuite_testcase_dict):
        #print('DEBUG: creating testsuite testcase for testsuite list: %s' % testsuite_list)
        json_object = {'testsuite':{}}
        testsuite_dict = json_object['testsuite']
        for testsuite in sorted(testsuite_list):
            testsuite_dict[testsuite] = {'testcase': {}}
            #print('DEBUG: testsuite: %s' % testsuite)
            #print('DEBUG: testsuite_testcase_dict[testsuite]: %s' % testsuite_testcase_dict[testsuite])
            testsuite_dict[testsuite]['testcase'] = self._create_testcase_dict(testsuite_testcase_dict[testsuite])
        return json_object

    def _create_testcase_dict(self, testcase_list):
        testcase_dict = {}
        for testcase in sorted(testcase_list):
            #testcase_key = '%s.%s' % (testsuite_name, testcase)
            testcase_dict[testcase] = {"testlog": "","testresult": ""}
        #print('DEBUG: testcase_dict: %s' % testcase_dict)
        return testcase_dict

    def _generate_testsuite_testcase_json_data_structure(self, testsuite_list, testsuite_testcase_dict):
        testsuite_testcase_list = self._create_testsuite_testcase_json_object(testsuite_list, testsuite_testcase_dict)
        return json.dumps(testsuite_testcase_list, sort_keys=True, indent=4)

    def _write_testsuite_testcase_json_data_structure_to_file(self, file_path, file_content):
        with open(file_path, 'w') as the_file:
            the_file.write(file_content)

    def _get_default_git_dir(self, git_dir):
        if git_dir == 'default':
            git_dir = os.path.join(self.base_path, 'test-result-log-git')
        return git_dir

    def _check_if_git_dir_exist(self, git_dir):
        return subprocess.run(["ls", '%s/.git' % git_dir])

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo, git_branch):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo, "-b", git_branch])

    def _remove_temporary_workspace_dir(self, workspace_dir):
        return subprocess.run(["rm", "-rf",  workspace_dir])

    def _checkout_git_repo(self, git_dir, git_branch):
        try:
            repo = GitRepo(git_dir, is_topdir=True)
        except GitError:
            print("Non-empty directory that is not a Git repository "
                   "at {}\nPlease specify an existing Git repository, "
                   "an empty directory or a non-existing directory "
                   "path.".format(git_dir))
        repo.run_cmd('checkout %s' % git_branch)

    def _load_test_module_file_with_json_into_dictionary(self, file):
        if os.path.exists(file):
            with open(file, "r") as f:
                return json.load(f)
        else:
            print('Cannot find file (%s)' % file)
            return None

    def _update_target_testresult_dictionary_with_status(self, target_testresult_dict, testsuite_list, testsuite_testcase_dict, testcase_status_dict):
        for testsuite in testsuite_list:
            testcase_list = testsuite_testcase_dict[testsuite]
            for testcase in testcase_list:
                testcase_status = testcase_status_dict[testcase]
                target_testresult_dict['testsuite'][testsuite]['testcase'][testcase]['testresult'] = testcase_status

    def _create_test_result_from_empty(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict):
        workspace_dir = self._create_temporary_workspace_dir()
        project_dir = os.path.join(workspace_dir, project)
        project_env_dir = self._create_project_environment_directory_path(project_dir, environment_list)
        pathlib.Path(project_env_dir).mkdir(parents=True, exist_ok=True)
        for testmodule in self._get_testmodule_list(testmodule_testsuite_dict):
            testsuite_list = testmodule_testsuite_dict[testmodule]
            module_json_structure = self._generate_testsuite_testcase_json_data_structure(testsuite_list, testsuite_testcase_dict)
            file_name = '%s.json' % testmodule
            file_path = os.path.join(project_env_dir, file_name)
            self._write_testsuite_testcase_json_data_structure_to_file(file_path, module_json_structure)
        self._push_testsuite_testcase_json_file_to_git_repo(workspace_dir, git_dir, git_branch)
        self._remove_temporary_workspace_dir(workspace_dir)

    def _create_test_result_from_existing(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict):
        self._checkout_git_repo(git_dir, git_branch)
        project_dir = os.path.join(git_dir, project)
        project_env_dir = self._create_project_environment_directory_path(project_dir, environment_list)
        pathlib.Path(project_env_dir).mkdir(parents=True, exist_ok=True)
        for testmodule in self._get_testmodule_list(testmodule_testsuite_dict):
            testsuite_list = testmodule_testsuite_dict[testmodule]
            module_json_structure = self._generate_testsuite_testcase_json_data_structure(testsuite_list, testsuite_testcase_dict)
            file_name = '%s.json' % testmodule
            file_path = os.path.join(project_env_dir, file_name)
            self._write_testsuite_testcase_json_data_structure_to_file(file_path, module_json_structure)
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)

    def create_test_result(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict):
        git_dir = self._get_default_git_dir(git_dir)
        # check if existing git_dir exist
        completed_process = self._check_if_git_dir_exist(git_dir)
        if completed_process.returncode == 0:
            self._create_test_result_from_existing(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict)
        else:
            self._create_test_result_from_empty(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict)

    def _write_log_file(self, file_path, logs):
        with open(file_path, 'a') as the_file:
            for line in logs:
                the_file.write(line + '\n')

    def update_test_result(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict, testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict):
        git_dir = self._get_default_git_dir(git_dir)
        self._checkout_git_repo(git_dir, git_branch)
        project_dir = os.path.join(git_dir, project)
        project_env_dir = self._create_project_environment_directory_path(project_dir, environment_list)
        for testmodule in self._get_testmodule_list(testmodule_testsuite_dict):
            testmodule_file = os.path.join(project_env_dir, '%s.json' % testmodule)
            target_testresult_dict = self._load_test_module_file_with_json_into_dictionary(testmodule_file)
            testsuite_list = testmodule_testsuite_dict[testmodule]
            self._update_target_testresult_dictionary_with_status(target_testresult_dict, testsuite_list, testsuite_testcase_dict, testcase_status_dict)
            self._write_testsuite_testcase_json_data_structure_to_file(testmodule_file, json.dumps(target_testresult_dict, sort_keys=True, indent=4))
        testcase_log_list = testcase_logs_dict.keys()
        for testcaselog in testcase_log_list:
            file_path = os.path.join(project_env_dir, '%s.log' % testcaselog)
            self._write_log_file(file_path, testcase_logs_dict[testcaselog])
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)
