import glob
import os
from jinja2 import Environment, FileSystemLoader
from testcasemgmt.gitstore import GitStore
from oeqa.core.runner import OETestResultJSONHelper

class TestResultView(object):

    def _check_if_existing_dir_list_contain_parent_for_new_dir(self, dir_list, new_dir):
        for existing_dir in dir_list:
            if existing_dir in new_dir:
                return True
        return False

    def _replace_existing_parent_dir_with_new_dir(self, dir_list, new_dir):
        return [new_dir if dir in new_dir else dir for dir in dir_list]

    def _get_test_report_directory_list(self, git_dir):
        exclude = ['.git', 'logs']
        report_dir_list = []
        for root, dirs, files in os.walk(git_dir, topdown=True):
            for dir in dirs:
                [dirs.remove(d) for d in list(dirs) if d in exclude]

            for dir in dirs:
                dirname = os.path.join(root, dir)
                if self._check_if_existing_dir_list_contain_parent_for_new_dir(report_dir_list, dirname):
                    report_dir_list = self._replace_existing_parent_dir_with_new_dir(report_dir_list, dirname)
                else:
                    report_dir_list.append(dirname)
        return report_dir_list

    def _get_list_of_test_result_files(self, report_dir):
        path_pattern = os.path.join(report_dir, '*.json')
        return glob.glob(path_pattern)

    def _get_testcase_result_dictionary(self, file):
        tresultjsonhelper = OETestResultJSONHelper()
        return tresultjsonhelper.load_testresult_file(file)

    def _get_full_testcase_result_dictionary(self, report_dir):
        full_testcase_result_dict = {}
        test_result_files = self._get_list_of_test_result_files(report_dir)
        for file in test_result_files:
            testcase_result_dict = self._get_testcase_result_dictionary(file)
            full_testcase_result_dict.update(testcase_result_dict)
        return full_testcase_result_dict

    # def _load_test_module_file_with_json_into_dictionary(self, file):
    #     with open(file, "r") as f:
    #         return json.load(f)

    # def _get_test_result_and_failed_error_testcase(self, test_result_dict, show_idle):
    #     count_idle = 0
    #     count_passed = 0
    #     count_failed = 0
    #     count_skipped = 0
    #     test_suites_dict = test_result_dict['testsuite']
    #     test_suites_list = test_suites_dict.keys()
    #     for suite in test_suites_list:
    #         test_cases_dict = test_suites_dict[suite]['testcase']
    #         test_cases_list = test_cases_dict.keys()
    #         failed_error_test_case_list = []
    #         for test_case in test_cases_list:
    #             test_status = test_cases_dict[test_case]['testresult']
    #             if test_status == 'FAILED' or test_status == 'ERROR':
    #                 failed_error_test_case_list.append(test_case)
    #                 count_failed += 1
    #             elif test_status == 'PASSED':
    #                 count_passed += 1
    #             elif test_status == 'SKIPPED':
    #                 count_skipped += 1
    #             elif test_status == "":
    #                 count_idle += 1
    #     if show_idle:
    #         return count_idle, count_passed, count_failed, count_skipped, failed_error_test_case_list
    #     else:
    #         return count_passed, count_failed, count_skipped, failed_error_test_case_list

    def _compute_test_result_percent_indicator(self, test_result):
        total_tested = test_result['passed'] + test_result['failed'] + test_result['skipped']
        test_result['passed_percent'] = 0
        test_result['failed_percent'] = 0
        test_result['skipped_percent'] = 0
        if total_tested > 0:
            test_result['passed_percent'] = format(test_result['passed']/total_tested * 100, '.2f')
            test_result['failed_percent'] = format(test_result['failed']/total_tested * 100, '.2f')
            test_result['skipped_percent'] = format(test_result['skipped']/total_tested * 100, '.2f')

    def _convert_test_result_value_to_string(self, test_result):
        test_result['passed_percent'] = str(test_result['passed_percent'])
        test_result['failed_percent'] = str(test_result['failed_percent'])
        test_result['skipped_percent'] = str(test_result['skipped_percent'])
        test_result['passed'] = str(test_result['passed'])
        test_result['failed'] = str(test_result['failed'])
        test_result['skipped'] = str(test_result['skipped'])
        if 'idle' in test_result:
            test_result['idle'] = str(test_result['idle'])
        if 'idle_percent' in test_result:
            test_result['idle_percent'] = str(test_result['idle_percent'])
        if 'complete' in test_result:
            test_result['complete'] = str(test_result['complete'])
        if 'complete_percent' in test_result:
            test_result['complete_percent'] = str(test_result['complete_percent'])

    def _get_max_string_len_from_test_result_list(self, test_result_list, key, default_max_len):
        max_len = default_max_len
        for test_result in test_result_list:
            value_len = len(test_result[key])
            if value_len > max_len:
                max_len = value_len
        return max_len

    def _map_raw_test_result_to_predefined_test_result_list(self, testcase_result_dict):
        passed_list = ['PASSED', 'passed']
        failed_list = ['FAILED', 'failed', 'ERROR', 'error']
        skipped_list = ['SKIPPED', 'skipped']
        test_result = {'passed': 0, 'failed': 0, 'skipped': 0, 'failed_testcases': []}

        for testcase in testcase_result_dict.keys():
            test_status = testcase_result_dict[testcase]
            if test_status in passed_list:
                test_result['passed'] += 1
            elif test_status in failed_list:
                test_result['failed'] += 1
                test_result['failed_testcases'].append(testcase)
            elif test_status in skipped_list:
                test_result['skipped'] += 1

        return test_result

    def _compile_test_result(self, testcase_result_dict):
        test_result = self._map_raw_test_result_to_predefined_test_result_list(testcase_result_dict)
        self._compute_test_result_percent_indicator(test_result)
        self._convert_test_result_value_to_string(test_result)
        return test_result

    def _get_test_component_environment_from_test_report_dir(self, git_repo, report_dir):
        test_component_environment = report_dir.replace(git_repo + '/', '')
        test_component = test_component_environment[:test_component_environment.find("/")]
        test_environment = test_component_environment.replace(test_component + '/', '')
        return test_component, test_environment, test_component_environment

    def _render_text_based_test_report(self, template_file_name, test_result_list, max_len_component, max_len_environment):
        script_path = os.path.dirname(os.path.realpath(__file__))
        file_loader = FileSystemLoader(script_path + '/template')
        env = Environment(loader=file_loader, trim_blocks=True)
        #template = env.get_template('test_report_full_text.txt')
        template = env.get_template(template_file_name)
        output = template.render(test_reports=test_result_list, max_len_component=max_len_component, max_len_environment=max_len_environment)
        print('Printing text-based test report:')
        print(output)

    def show_text_based_test_report(self, git_repo):
        report_dir_list = self._get_test_report_directory_list(git_repo)
        print('report_dir_list : %s' % report_dir_list)
        test_result_list = []
        for report_dir in report_dir_list:
            print('Compiling test result for %s:' % report_dir)
            template_file_name = 'test_report_full_text.txt'
            testcase_result_dict = self._get_full_testcase_result_dictionary(report_dir)
            test_result = self._compile_test_result(testcase_result_dict)
            test_component, test_environment, test_component_environment = self._get_test_component_environment_from_test_report_dir(git_repo, report_dir)
            test_result['test_component'] = test_component
            test_result['test_environment'] = test_environment
            test_result['test_component_environment'] = test_component_environment
            test_result_list.append(test_result)
        max_len_component = self._get_max_string_len_from_test_result_list(test_result_list, 'test_component', len('test_component'))
        max_len_environment = self._get_max_string_len_from_test_result_list(test_result_list, 'test_environment', len('test_environment'))
        self._render_text_based_test_report(template_file_name, test_result_list, max_len_component, max_len_environment)

def view(args, logger):
    gitstore = GitStore()
    if gitstore.checkout_git_branch(args.git_repo, args.git_branch):
        testresultview = TestResultView()
        testresultview.show_text_based_test_report(args.git_repo)
    return 0

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('view', help='View text-based summary test report',
                                         description='View text-based summary test report',
                                         group='view')
    parser_build.set_defaults(func=view)
    parser_build.add_argument('git_branch', help='Git branch to be used to compute test summary report')
    parser_build.add_argument('-g', '--git_repo', default='default', help='(Optional) Full path to the git repository to be used to compute the test summary report, default will be <top_dir>/test-result-log.git')
