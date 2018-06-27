import glob
import os
import json
from jinja2 import Environment, FileSystemLoader
from testresultlog.testresultgitstore import TestResultGitStore

class TestResultViewer(object):

    def _check_if_existing_dir_list_contain_parent_for_new_dir(self, dir_list, new_dir):
        for existing_dir in dir_list:
            if existing_dir in new_dir:
                print('%s is parent for %s' % (existing_dir, new_dir))
                return True
        return False

    def _replace_existing_parent_dir_with_new_dir(self, dir_list, new_dir):
        return [new_dir if dir in new_dir else dir for dir in dir_list]

    def get_test_report_directory_list(self, git_dir):
        exclude = ['.git']
        report_dir_list = []
        for root, dirs, files in os.walk(git_dir, topdown=True):
            for dir in dirs:
                [dirs.remove(d) for d in list(dirs) if d in exclude]

            for dir in dirs:
                print(os.path.join(root, dir))
                dirname = os.path.join(root, dir)
                if self._check_if_existing_dir_list_contain_parent_for_new_dir(report_dir_list, dirname):
                    report_dir_list = self._replace_existing_parent_dir_with_new_dir(report_dir_list, dirname)
                else:
                    report_dir_list.append(dirname)
        print('report_dir_list: %s' % report_dir_list)
        return report_dir_list

    def _get_list_of_test_result_files(self, report_dir):
        path_pattern = os.path.join(report_dir, '*.json')
        return glob.glob(path_pattern)

    def _load_test_module_file_with_json_into_dictionary(self, file):
        with open(file, "r") as f:
            return json.load(f)

    def _get_test_result_and_failed_error_testcase(self, test_result_dict):
        count_passed = 0
        count_failed = 0
        count_skipped = 0
        test_suites_dict = test_result_dict['testsuite']
        test_suites_list = test_suites_dict.keys()
        for suite in test_suites_list:
            test_cases_dict = test_suites_dict[suite]['testcase']
            test_cases_list = test_cases_dict.keys()
            failed_error_test_case_list = []
            for test_case in test_cases_list:
                test_status = test_cases_dict[test_case]['testresult']
                if test_status == 'FAILED' or test_status == 'ERROR':
                    failed_error_test_case_list.append(test_case)
                    count_failed += 1
                elif test_status == 'PASSED':
                    count_passed += 1
                elif test_status == 'SKIPPED':
                    count_skipped += 1
        return count_passed, count_failed, count_skipped, failed_error_test_case_list

    def compile_test_result_for_test_report_directory(self, report_dir):
        test_result_files = self._get_list_of_test_result_files(report_dir)
        test_result = {'passed':0, 'failed':0, 'skipped':0}
        total_failed_error_test_case_list = []
        for file in test_result_files:
            test_result_dict = self._load_test_module_file_with_json_into_dictionary(file)
            count_passed, count_failed, count_skipped, failed_error_test_case_list = self._get_test_result_and_failed_error_testcase(test_result_dict)
            test_result['passed'] += count_passed
            test_result['failed'] += count_failed
            test_result['skipped'] += count_skipped
            total_failed_error_test_case_list = total_failed_error_test_case_list + failed_error_test_case_list
        print('test_result: %s' % test_result)
        print('total_failed_error_test_case_list: %s' % total_failed_error_test_case_list)
        return test_result, total_failed_error_test_case_list

    def get_test_component_environment_from_test_report_dir(self, git_repo, report_dir):
        test_component_environment = report_dir.replace(git_repo + '/', '')
        test_component = test_component_environment[:test_component_environment.find("/")]
        test_environment = test_component_environment.replace(test_component + '/', '')
        print('test_component: %s' % test_component)
        print('test_environment: %s' % test_environment)
        return test_component, test_environment, test_component_environment

    def create_text_based_test_report(self, test_result_list):
        script_path = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(script_path + '/template')
        # 'test_report_full_text.txt'
        env = Environment(loader=file_loader)
        template = env.get_template('test_report_full_text.txt')
        #farms = [{'name':'Joshua', 'animal':'cow'}, {'name':'Mason', 'animal':'pig'}, {'name':'Hewson', 'animal':'turtle'}]
        output = template.render(test_reports=test_result_list)
        print('Printing text-based test report:')
        print(output)

def main(args):
    testresultstore = TestResultGitStore()
    if testresultstore.checkout_git_branch(args.git_repo, args.git_branch):
        # get list of directory for test summary compilation
        # compile test summary for each directory
        # create test summary based on report template
        testviewer = TestResultViewer()
        report_dir_list = testviewer.get_test_report_directory_list(args.git_repo)
        test_result_list = []
        for report_dir in report_dir_list:
            print('Compiling test result for %s:' % report_dir)
            test_result, total_failed_error_test_case_list = testviewer.compile_test_result_for_test_report_directory(report_dir)
            test_component, test_environment, test_component_environment = testviewer.get_test_component_environment_from_test_report_dir(args.git_repo, report_dir)
            test_result['test_component'] = test_component
            test_result['test_environment'] = test_environment
            test_result['test_component_environment'] = test_component_environment
            test_result_list.append(test_result)
        testviewer.create_text_based_test_report(test_result_list)

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('view', help='View summary test result',
                                         description='View summary test result')
    parser_build.set_defaults(func=main)
    parser_build.add_argument('-g', '--git_repo', required=False, default='default', help='(Optional) Git repository to be view summary test result ,default will be /poky/test-result-log.git')
    parser_build.add_argument('-b', '--git_branch', required=True, help='Git branch to be updated with test result')
