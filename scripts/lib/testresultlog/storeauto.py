# test case management tool - store automated test result
#
# Copyright (c) 2018, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
from testresultlog.gitstore import GitStore
from testresultlog.oeqatestdiscover import OeqaTestDiscover
from testresultlog.oeqalogparser import OeqaLogParser

class StoreAuto(object):

    def _get_testsuite_from_testcase(self, testcase):
        testsuite = testcase[0:testcase.rfind(".")]
        return testsuite

    def _get_testmodule_from_testsuite(self, testsuite):
        testmodule = testsuite[0:testsuite.find(".")]
        return testmodule

    def _remove_testsuite_from_testcase(self, testcase, testsuite):
        testsuite = testsuite + '.'
        testcase_remove_testsuite = testcase.replace(testsuite, '')
        return testcase_remove_testsuite

    def _add_new_environment_to_environment_list(self, environment_list, new_environment):
        if len(new_environment) > 0 and new_environment not in environment_list:
            if len(environment_list) == 0:
                environment_list = new_environment
            else:
                environment_list = '%s,%s' % (environment_list, new_environment)
        return environment_list

    def get_environment_list_for_test_log(self, log_file, log_file_source, environment_list, oeqa_logparser):
        if log_file_source == 'runtime':
            runtime_image_env = oeqa_logparser.get_runtime_test_image_environment(log_file)
            runtime_qemu_env = oeqa_logparser.get_runtime_test_qemu_environment(log_file)
            environment_list = self._add_new_environment_to_environment_list(environment_list, runtime_image_env)
            environment_list = self._add_new_environment_to_environment_list(environment_list, runtime_qemu_env)
        return environment_list.split(",")

    def get_testsuite_testcase_dictionary(self, testcase_dir):
        oeqatestdiscover = OeqaTestDiscover()
        testcase_list = oeqatestdiscover.get_oeqa_testcase_list(testcase_dir)
        testsuite_testcase_dict = {}
        for testcase in testcase_list:
            testsuite = self._get_testsuite_from_testcase(testcase)
            if testsuite in testsuite_testcase_dict:
                testsuite_testcase_dict[testsuite].append(testcase)
            else:
                testsuite_testcase_dict[testsuite] = [testcase]
        return testsuite_testcase_dict

    def get_testmodule_testsuite_dictionary(self, testsuite_testcase_dict):
        testsuite_list = testsuite_testcase_dict.keys()
        testmodule_testsuite_dict = {}
        for testsuite in testsuite_list:
            testmodule = self._get_testmodule_from_testsuite(testsuite)
            if testmodule in testmodule_testsuite_dict:
                testmodule_testsuite_dict[testmodule].append(testsuite)
            else:
                testmodule_testsuite_dict[testmodule] = [testsuite]
        return testmodule_testsuite_dict

    def get_testcase_failed_or_error_logs_dictionary(self, log_file, testcase_status_dict):
        oeqalogparser = OeqaLogParser()
        testcase_list = testcase_status_dict.keys()
        testcase_failed_or_error_logs_dict = {}
        for testcase in testcase_list:
            test_status = testcase_status_dict[testcase]
            if test_status == 'FAILED' or test_status == 'ERROR':
                testsuite = self._get_testsuite_from_testcase(testcase)
                testfunction = self._remove_testsuite_from_testcase(testcase, testsuite)
                logs = oeqalogparser.get_test_log(log_file, test_status, testfunction, testsuite)
                testcase_failed_or_error_logs_dict[testcase] = logs
        return testcase_failed_or_error_logs_dict

def storeauto(args, logger):
    logger.info('Gathering test result and log data')
    oeqa_logparser = OeqaLogParser()
    testcase_status_dict = oeqa_logparser.get_test_status(args.log_file)
    logger.debug('Received testcase status dictionary %s' % testcase_status_dict)

    store_auto = StoreAuto()
    logger.debug('Getting test environment and breaking down test result & log data')
    environment_list = store_auto.get_environment_list_for_test_log(args.log_file, args.source, args.environment_list, oeqa_logparser)
    logger.debug('Received environment list %s' % environment_list)
    testsuite_testcase_dict = store_auto.get_testsuite_testcase_dictionary(args.case_dir)
    logger.debug('Received testsuite testcase dictionary %s' % testsuite_testcase_dict)
    testmodule_testsuite_dict = store_auto.get_testmodule_testsuite_dictionary(testsuite_testcase_dict)
    logger.debug('Received testmodule testsuite dictionary %s' % testmodule_testsuite_dict)
    test_logs_dict = store_auto.get_testcase_failed_or_error_logs_dictionary(args.log_file, testcase_status_dict)
    logger.debug('Received test logs dictionary %s' % test_logs_dict)

    git_store = GitStore()
    logger.info('Storing test result and log data')
    git_store.smart_create_update_automated_test_result(args.git_repo, args.git_branch, args.top_folder_name, environment_list, testmodule_testsuite_dict,
                                                       testsuite_testcase_dict, testcase_status_dict, test_logs_dict, logger)
    return 0

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('store-auto', help='Store OEQA automated test status & log into git repository',
                                         description='Store OEQA automated test status & log into git repository',
                                         group='store')
    parser_build.set_defaults(func=storeauto)
    parser_build.add_argument('top_folder_name', help='Folder name used to create the top folder inside git repository that store the test status & log')
    parser_build.add_argument('git_branch', help='Git branch to store the test status & log')
    parser_build.add_argument('log_file', help='Full path to the OEQA automated test log file to be used for test result storing')
    SOURCES = ('runtime', 'selftest', 'sdk', 'sdkext')
    parser_build.add_argument('source', choices=SOURCES,
    help='Selected testcase sources to be used for OEQA testcase discovery and testcases discovered will be used as the base testcases for storing test status & log. '
         '"runtime" will search testcase available in meta/lib/oeqa/runtime/cases. '
         '"selftest" will search testcase available in meta/lib/oeqa/selftest/cases. '
         '"sdk" will search testcase available in meta/lib/oeqa/sdk/cases. '
         '"sdkext" will search testcase available in meta/lib/oeqa/sdkext/cases. ')
    parser_build.add_argument('-g', '--git_repo', default='', help='(Optional) Full path to the git repository used for storage, default will be <top_dir>/test-result-log.git')
    parser_build.add_argument('-e', '--environment_list', default='', help='(Optional) List of environment separated by comma (",") used to create the subfolder(s) under the top_folder_name to store test status & log')
