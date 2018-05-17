import os
import json
import subprocess
import scriptpath
scriptpath.add_bitbake_lib_path()
scriptpath.add_oe_lib_path()
from oeqa.utils.git import GitRepo, GitError
from testresultlog.testresultlogconfigparser import TestResultLogConfigParser
from testresultlog.testlogparser import TestLogParser

class TestResultGitUpdator(object):

    def _checkout_git_repo_for_update(self, git_dir, git_branch):
        try:
            repo = GitRepo(git_dir, is_topdir=True)
        except GitError:
            print("Non-empty directory that is not a Git repository "
                   "at {}\nPlease specify an existing Git repository, "
                   "an empty directory or a non-existing directory "
                   "path.".format(git_dir))
        repo.run_cmd('checkout %s' % git_branch)

    def _get_test_module_name_from_test_function(self, test_function):
        test_module_name = test_function[0:test_function.find(".")]
        return test_module_name

    def _get_test_class_name_from_test_function(self, test_function):
        test_function_remove_module = test_function[test_function.find(".")+1:]
        test_moduleclass_name = test_function_remove_module[0:test_function_remove_module.find(".")]
        return test_moduleclass_name

    def _remove_test_module_class_name_from_test_function(self, test_function, test_module_class_name):
        test_module_class_name = test_module_class_name + '.'
        test_function_remove_module_class = test_function.replace(test_module_class_name, '')
        return test_function_remove_module_class

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
            test_class_name = self._get_test_class_name_from_test_function(test_funtion)
            test_module_class_name = '%s.%s' % (test_module, test_class_name)
            testresult_dict['testsuite'][test_module_class_name]['testcase'][test_funtion]['testresult'] = test_function_status

    def _write_testsuite_testcase_json_data_structure_to_file(self, file_path, file_content):
        with open(file_path, 'w') as the_file:
            the_file.write(file_content)

    def _push_testsuite_testcase_json_file_to_git_repo(self, file_dir, git_repo, git_branch):
        return subprocess.run(["oe-git-archive", file_dir, "-g", git_repo, "-b", git_branch])

    def _get_git_repo_dir(self, script_path, git_dir):
        if git_dir == 'default':
            script_path = os.path.join(script_path, '..')
            git_dir = os.path.join(script_path, 'test-result-log-git')
        return git_dir

    def _update_test_result_to_json_files_inside_git_repository(self, testmodule_testfunction_dict, test_function_status_dict, work_dir):
        test_module_list = testmodule_testfunction_dict.keys()
        for test_module in test_module_list:
            test_module_file = os.path.join(work_dir, 'testresult_%s.json' % test_module)
            if os.path.exists(test_module_file):
                # print('Found file (%s)' % test_module_file)
                testresult_dict = self._load_test_module_file_with_json_into_dictionary(test_module_file)
                # print('Test Result Dictionary : %s' % testresult_dict)
                self._update_testresult_dictionary(testresult_dict, test_module, testmodule_testfunction_dict,
                                                   test_function_status_dict)
                # print('Updated Test Result Dictionary : %s' % testresult_dict)
                self._write_testsuite_testcase_json_data_structure_to_file(test_module_file,
                                                                           json.dumps(testresult_dict, sort_keys=True,
                                                                                      indent=4))
            else:
                print('Cannot find file (%s)' % test_module_file)

    def _write_log_file(self, file_path, logs):
        with open(file_path, 'a') as the_file:
            for line in logs:
                the_file.write(line + '\n')

    def _capture_test_fail_log_into_log_files(self, log_file, test_function_status_dict, work_dir):
        testlogparser = TestLogParser()
        test_function_list = test_function_status_dict.keys()
        for test_func in test_function_list:
            test_status = test_function_status_dict[test_func]
            if test_status == 'FAILED' or test_status == 'ERROR':
                module_name = self._get_test_module_name_from_test_function(test_func)
                class_name = self._get_test_class_name_from_test_function(test_func)
                module_class_name = '%s.%s' % (module_name, class_name)
                func_name = self._remove_test_module_class_name_from_test_function(test_func, module_class_name)
                logs = testlogparser.get_test_log(log_file, test_status, func_name, module_class_name)
                #print(logs)
                file_path = os.path.join(work_dir, '%s.%s.log' % (module_class_name, func_name))
                self._write_log_file(file_path, logs)

    def update_test_result(self, log_file, test_function_status_dict, script_path, git_dir, git_branch, work_dir):
        git_dir = self._get_git_repo_dir(script_path, git_dir)
        self._checkout_git_repo_for_update(git_dir, git_branch)
        work_dir = os.path.join(git_dir, work_dir)
        testmodule_testfunction_dict = self._get_testmodule_testfunction_dictionary(test_function_status_dict)
        self._update_test_result_to_json_files_inside_git_repository(testmodule_testfunction_dict, test_function_status_dict, work_dir)
        self._capture_test_fail_log_into_log_files(log_file, test_function_status_dict, work_dir)
        self._push_testsuite_testcase_json_file_to_git_repo(git_dir, git_dir, git_branch)

def main(args):
    scripts_path = os.path.dirname(os.path.realpath(__file__))
    testplan_conf = os.path.join(scripts_path, 'conf/testplan.conf')

    testlogparser = TestLogParser()
    test_function_status_dict = testlogparser.get_test_status(args.log_file)
    print('DEGUG: test_function_status_dict: %s' % test_function_status_dict)
    testresultupdator = TestResultGitUpdator()
    testresultupdator.update_test_result(args.log_file, test_function_status_dict, args.script_path, args.git_repo, args.git_branch, args.work_dir)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('update', help='Update test result status into the specified test result template',
                                         description='Update test result status from the test log into the specified test result template')
    parser_build.set_defaults(func=main)
    parser_build.add_argument('-l', '--log_file', required=True, help='Full path to the test log file to be used for test result update')
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be updated ,default will be /poky/test-result-log-git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be updated with test result')
    parser_build.add_argument('-w', '--work_dir', required=True, help='Working directory from within the selected git repository to update with test result')