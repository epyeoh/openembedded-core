import tempfile
import os
import pathlib
import json
import subprocess
import shutil
import scriptpath
scriptpath.add_bitbake_lib_path()
scriptpath.add_oe_lib_path()
from oeqa.utils.git import GitRepo, GitError

class GitStore(object):

    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.base_path = self.script_path + '/../../..'

    def _get_project_environment_directory_path(self, project_dir, test_environment_list):
        project_env_dir = project_dir
        for env in test_environment_list:
            project_env_dir = os.path.join(project_env_dir, env)
        return project_env_dir

    def _get_testmodule_list(self, testmodule_testsuite_dict):
        return sorted(list(testmodule_testsuite_dict.keys()))

    def _get_testcase_list(self, testsuite_list, testsuite_testcase_dict):
        testcase_list = []
        for testsuite in sorted(testsuite_list):
            if testsuite in testsuite_testcase_dict:
                for testcase in testsuite_testcase_dict[testsuite]:
                    testcase_list.append(testcase)
        return testcase_list

    def _get_testcase_status(self, testcase, testcase_status_dict):
        if testcase in testcase_status_dict:
            return testcase_status_dict[testcase]
        return ""

    def _create_testcase_dict(self, testcase_list, testcase_status_dict):
        testcase_dict = {}
        for testcase in sorted(testcase_list):
            testcase_status = self._get_testcase_status(testcase, testcase_status_dict)
            testcase_dict[testcase] = {"testresult": testcase_status,"bugs": ""}
        return testcase_dict

    def _create_testsuite_testcase_teststatus_json_object(self, testsuite_list, testsuite_testcase_dict, testcase_status_dict):
        json_object = {'testsuite':{}}
        testsuite_dict = json_object['testsuite']
        for testsuite in sorted(testsuite_list):
            testsuite_dict[testsuite] = {'testcase': {}}
            testsuite_dict[testsuite]['testcase'] = self._create_testcase_dict(testsuite_testcase_dict[testsuite], testcase_status_dict)
        return json_object

    def _create_testsuite_json_formatted_string(self, testsuite_list, testsuite_testcase_dict, testcase_status_dict):
        testsuite_testcase_list = self._create_testsuite_testcase_teststatus_json_object(testsuite_list, testsuite_testcase_dict, testcase_status_dict)
        return json.dumps(testsuite_testcase_list, sort_keys=True, indent=4)

    def _write_testsuite_testcase_json_formatted_string_to_file(self, file_path, file_content):
        with open(file_path, 'w') as the_file:
            the_file.write(file_content)

    def _write_log_file(self, file_path, logs):
        with open(file_path, 'w') as the_file:
            for line in logs:
                the_file.write(line + '\n')

    def _write_test_log_files_for_list_of_testcase(self, file_dir, testcase_list, testcase_logs_dict):
        for testcase in testcase_list:
            if testcase in testcase_logs_dict:
                file_path = os.path.join(file_dir, '%s.log' % testcase)
                self._write_log_file(file_path, testcase_logs_dict[testcase])

    def _copy_files_from_source_to_destination_dir(self, source_dir, destination_dir):
        if os.path.exists(source_dir) and os.path.exists(destination_dir):
            for item in os.listdir(source_dir):
                s = os.path.join(source_dir, item)
                d = os.path.join(destination_dir, item)
                shutil.copy2(s, d)

    def _load_test_module_file_with_json_into_dictionary(self, file):
        if os.path.exists(file):
            with open(file, "r") as f:
                return json.load(f)
        else:
            print('Cannot find file (%s)' % file)
            return None

    def _get_testcase_log_need_removal_list(self, testcase, cur_testcase_status, next_testcase_status, testcase_log_remove_list):
        if cur_testcase_status == 'FAILED' or cur_testcase_status == 'ERROR':
            if next_testcase_status == 'PASSED' or next_testcase_status == 'SKIPPED':
                testcase_log_remove_list.append(testcase)

    def _update_target_testresult_dictionary_with_status(self, target_testresult_dict, testsuite_list, testsuite_testcase_dict,
                                                         testcase_status_dict, testcase_log_remove_list):
        for testsuite in testsuite_list:
            testcase_list = testsuite_testcase_dict[testsuite]
            for testcase in testcase_list:
                if testcase in testcase_status_dict:
                    cur_testcase_status = target_testresult_dict['testsuite'][testsuite]['testcase'][testcase]['testresult']
                    next_testcase_status = testcase_status_dict[testcase]
                    self._get_testcase_log_need_removal_list(testcase, cur_testcase_status, next_testcase_status, testcase_log_remove_list)
                    target_testresult_dict['testsuite'][testsuite]['testcase'][testcase]['testresult'] = next_testcase_status

    def _remove_test_log_files(self, file_dir, testcase_log_remove_list):
        for testcase_log_remove in testcase_log_remove_list:
            file_remove_path = os.path.join(file_dir, '%s.log' % testcase_log_remove)
            if os.path.exists(file_remove_path):
                os.remove(file_remove_path)

    def _check_if_dir_contain_project_and_environment_directory(self, git_dir, project, environment_list):
        project_env_dir = self._get_project_environment_directory(git_dir, project, environment_list)
        completed_process = subprocess.run(["ls", project_env_dir])
        if completed_process.returncode == 0:
            return True
        else:
            return False

    def _git_init(self, git_dir):
        try:
            repo = GitRepo(git_dir, is_topdir=True)
        except GitError:
            print("Non-empty directory that is not a Git repository "
                   "at {}\nPlease specify an existing Git repository, "
                   "an empty directory or a non-existing directory "
                   "path.".format(git_dir))
        return repo

    def _run_git_cmd(self, repo, cmd):
        try:
            output = repo.run_cmd(cmd)
            return True, output
        except GitError:
            return False, None

    def _check_if_git_dir_and_git_branch_exist(self, git_dir, git_branch):
        completed_process = subprocess.run(["ls", '%s/.git' % git_dir])
        if not completed_process.returncode == 0:
            return False
        repo = self._git_init(git_dir)
        return self._git_checkout_git_repo(repo, git_branch)[0]

    def _git_checkout_git_repo(self, repo, git_branch):
        cmd = 'checkout %s' % git_branch
        return self._run_git_cmd(repo, cmd)

    def _create_temporary_workspace_dir(self):
        return tempfile.mkdtemp(prefix='testresultlog.')

    def _remove_temporary_workspace_dir(self, workspace_dir):
        return subprocess.run(["rm", "-rf",  workspace_dir])

    def _get_project_environment_directory(self, top_dir, project, environment_list):
        project_dir = os.path.join(top_dir, project)
        project_env_dir = self._get_project_environment_directory_path(project_dir, environment_list)
        return project_env_dir

    def _create_project_environment_directory_structure(self, top_dir, project, environment_list):
        project_env_dir = self._get_project_environment_directory(top_dir, project, environment_list)
        pathlib.Path(project_env_dir).mkdir(parents=True, exist_ok=True)
        return project_env_dir

    def _create_testmodule_and_test_log_files_to_directory(self, directory, testmodule_testsuite_dict, testsuite_testcase_dict,
                                                           testcase_status_dict, testcase_logs_dict):
        for testmodule in self._get_testmodule_list(testmodule_testsuite_dict):
            testsuite_list = testmodule_testsuite_dict[testmodule]
            testsuite_json_structure = self._create_testsuite_json_formatted_string(testsuite_list, testsuite_testcase_dict, testcase_status_dict)
            file_name = '%s.json' % testmodule
            file_path = os.path.join(directory, file_name)
            self._write_testsuite_testcase_json_formatted_string_to_file(file_path, testsuite_json_structure)
            testcase_list = self._get_testcase_list(testsuite_list, testsuite_testcase_dict)
            self._write_test_log_files_for_list_of_testcase(directory, testcase_list, testcase_logs_dict)

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo, git_branch):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo, "-b", git_branch])

    def _create_automated_test_result_from_empty_git(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                     testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict):
        workspace_dir = self._create_temporary_workspace_dir()
        project_env_dir = self._create_project_environment_directory_structure(workspace_dir, project, environment_list)
        self._create_testmodule_and_test_log_files_to_directory(project_env_dir, testmodule_testsuite_dict, testsuite_testcase_dict,
                                                                testcase_status_dict, testcase_logs_dict)
        self._push_testsuite_testcase_json_file_to_git_repo(workspace_dir, git_dir, git_branch)
        self._remove_temporary_workspace_dir(workspace_dir)

    def _create_automated_test_result_from_existing_git(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                        testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict):
        project_env_dir = self._create_project_environment_directory_structure(git_dir, project, environment_list)
        self._create_testmodule_and_test_log_files_to_directory(project_env_dir, testmodule_testsuite_dict, testsuite_testcase_dict,
                                                                testcase_status_dict, testcase_logs_dict)
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)

    def _load_testmodule_file_and_update_test_result(self, project_env_dir, testmodule_testsuite_dict, testsuite_testcase_dict,
                                                     testcase_status_dict, testcase_logs_dict, testcase_log_remove_list):
        for testmodule in self._get_testmodule_list(testmodule_testsuite_dict):
            testmodule_file = os.path.join(project_env_dir, '%s.json' % testmodule)
            target_testresult_dict = self._load_test_module_file_with_json_into_dictionary(testmodule_file)
            testsuite_list = testmodule_testsuite_dict[testmodule]
            self._update_target_testresult_dictionary_with_status(target_testresult_dict, testsuite_list, testsuite_testcase_dict,
                                                                  testcase_status_dict, testcase_log_remove_list)
            self._write_testsuite_testcase_json_formatted_string_to_file(testmodule_file, json.dumps(target_testresult_dict, sort_keys=True, indent=4))
            testcase_list = self._get_testcase_list(testsuite_list, testsuite_testcase_dict)
            self._write_test_log_files_for_list_of_testcase(project_env_dir, testcase_list, testcase_logs_dict)

    def _update_automated_test_result(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                      testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict):
        print('Updating test result for environment list: %s' % environment_list)
        repo = self._git_init(git_dir)
        self._git_checkout_git_repo(repo, git_branch)
        project_env_dir = self._get_project_environment_directory(git_dir, project, environment_list)
        testcase_log_remove_list = []
        self._load_testmodule_file_and_update_test_result(project_env_dir, testmodule_testsuite_dict, testsuite_testcase_dict,
                                                          testcase_status_dict, testcase_logs_dict, testcase_log_remove_list)
        self._remove_test_log_files(project_env_dir, testcase_log_remove_list)
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)

    def smart_create_update_automated_test_result(self, git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                  testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict):
        print('Creating/Updating test result for environment list: %s' % environment_list)
        if self._check_if_git_dir_and_git_branch_exist(git_dir, git_branch):
            repo = self._git_init(git_dir)
            self._git_checkout_git_repo(repo, git_branch)
            print('Found git_dir and git_branch: %s %s' % (git_dir, git_branch))
            print('Entering git_dir: %s' % git_dir)
            if self._check_if_dir_contain_project_and_environment_directory(git_dir, project, environment_list):
                print('Found project and environment inside git_dir: %s' % git_dir)
                print('Updating test result')
                self._update_automated_test_result(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                   testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict)
            else:
                print('Could not find project and environment inside git_dir: %s' % git_dir)
                print('Creating project and environment inside git_dir: %s' % git_dir)
                self._create_automated_test_result_from_existing_git(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                                     testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict)
        else:
            print('Could not find git_dir or git_branch: %s %s' % (git_dir, git_branch))
            print('Creating git_dir, git_branch, project, and environment: %s' % git_dir)
            self._create_automated_test_result_from_empty_git(git_dir, git_branch, project, environment_list, testmodule_testsuite_dict,
                                                              testsuite_testcase_dict, testcase_status_dict, testcase_logs_dict)
