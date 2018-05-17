import glob
import os
import json
import scriptpath
scriptpath.add_bitbake_lib_path()
scriptpath.add_oe_lib_path()
from oeqa.utils.git import GitRepo, GitError

class TestResultViewer(object):

    def _get_git_repo_dir(self, script_path, git_dir):
        if git_dir == 'default':
            script_path = os.path.join(script_path, '..')
            git_dir = os.path.join(script_path, 'test-result-log-git')
        return git_dir

    def _checkout_git_repo_for_update(self, git_dir, git_branch):
        try:
            repo = GitRepo(git_dir, is_topdir=True)
        except GitError:
            print("Non-empty directory that is not a Git repository "
                   "at {}\nPlease specify an existing Git repository, "
                   "an empty directory or a non-existing directory "
                   "path.".format(git_dir))
        repo.run_cmd('checkout %s' % git_branch)

    def _get_list_of_test_result_files(self, work_dir):
        path_pattern = os.path.join(work_dir, '*.json')
        return glob.glob(path_pattern)

    def _load_test_module_file_with_json_into_dictionary(self, file):
        with open(file, "r") as f:
            return json.load(f)

    def _insert_failed_error_test_status_from_testcases(self, test_cases_dict, failed_error_test_case_status_dict):
        test_cases_list = test_cases_dict.keys()
        #failed_error_test_case_status_dict = {}
        for test_case in test_cases_list:
            test_status = test_cases_dict[test_case]['testresult']
            if test_status == 'FAILED' or test_status == 'ERROR':
                failed_error_test_case_status_dict[test_case] = test_status

    def _insert_failed_error_test_status_from_testsuites(self, test_result_dict, failed_error_test_case_status_dict):
        test_suites_dict = test_result_dict['testsuite']
        test_suites_list = test_suites_dict.keys()
        for suite in test_suites_list:
            test_cases_dict = test_suites_dict[suite]['testcase']
            self._insert_failed_error_test_status_from_testcases(test_cases_dict, failed_error_test_case_status_dict)

    def _get_test_log(self, work_dir, test_case):
        test_log_file = os.path.join(work_dir, '%s.log' % test_case)
        print('========== FAILED | ERROR logs ==========')
        with open(test_log_file, "r") as f:
            for line in f:
                print(line)

    def get_all_failed_error_test_status_log(self, script_path, git_dir, git_branch, work_dir):
        git_dir = self._get_git_repo_dir(script_path, git_dir)
        self._checkout_git_repo_for_update(git_dir, git_branch)
        work_dir = os.path.join(git_dir, work_dir)
        test_result_files = self._get_list_of_test_result_files(work_dir)
        failed_error_test_case_status_dict = {}
        for file in test_result_files:
            test_result_dict = self._load_test_module_file_with_json_into_dictionary(file)
            self._insert_failed_error_test_status_from_testsuites(test_result_dict, failed_error_test_case_status_dict)
        failed_error_test_list = failed_error_test_case_status_dict.keys()
        print('========== Listing all FAILED | ERROR test cases ==========')
        for failed_error_test in failed_error_test_list:
            print('%s : %s' % (failed_error_test, failed_error_test_case_status_dict[failed_error_test]))
            #self._get_test_log(work_dir, failed_error_test)

def main(args):
    testresultviewer = TestResultViewer()
    testresultviewer.get_all_failed_error_test_status_log(args.script_path, args.git_repo, args.git_branch, args.work_dir)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('view', help='View test result status for failed or error test cases',
                                         description='View test result status for failed or error test cases')
    parser_build.set_defaults(func=main)
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be updated ,default will be /poky/test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be updated with test result')
    parser_build.add_argument('-w', '--work_dir', required=True, help='Working directory from within the selected git repository to view test result')