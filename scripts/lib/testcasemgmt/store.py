# test case management tool - store test result & log
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
from testcasemgmt.gitstore import GitStore

def store(args, logger):
    env_list = []
    if len(args.environment_list) > 0:
        env_list = args.environment_list.split(",")
    gitstore = GitStore()
    gitstore.store_test_result(logger, args.testresult_dir, args.git_repo, args.git_branch, args.top_folder, env_list)
    return 0

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('store', help='Store OEQA test result & log into git repository',
                                         description='Store OEQA test result & log into git repository',
                                         group='store')
    parser_build.set_defaults(func=store)
    parser_build.add_argument('testresult_dir',
                              help='Directory to the test result & log files to be stored')
    parser_build.add_argument('top_folder',
                              help='Top folder to be created inside the git repository')
    parser_build.add_argument('git_branch', help='Git branch to store the test result & log')
    parser_build.add_argument('-g', '--git_repo', default='',
                              help='(Optional) Full path to the git repository used for storage, default will be <top_dir>/test-result-log.git')
    parser_build.add_argument('-e', '--environment_list', default='',
                              help='(Optional) List of environment separated by comma (",") used to create the subfolder(s) under the top_folder_name to store test status & log')
