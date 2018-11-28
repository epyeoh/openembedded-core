# test case management tool - store test result
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
    gitstore = GitStore(args.git_dir, args.git_branch)
    gitstore.store_test_result(logger, args.source_dir, args.git_sub_dir, args.overwrite_result)
    return 0

def register_commands(subparsers):
    """Register subcommands from this plugin"""
    parser_build = subparsers.add_parser('store', help='Store test result files into git repository.',
                                         description='Store test result files into git repository.',
                                         group='store')
    parser_build.set_defaults(func=store)
    parser_build.add_argument('source_dir',
                              help='Source directory that contain the test result files to be stored.')
    parser_build.add_argument('git_branch', help='Git branch used to store the test result files.')
    parser_build.add_argument('-d', '--git_dir', default='',
                              help='(Optional) Destination directory to be used or created as git repository '
                                   'to store the test result files from the source directory. '
                                   'Default location for destination directory will be <top_dir>/testresults.git.')
    parser_build.add_argument('-s', '--git_sub_dir', default='',
                              help='(Optional) Additional sub directory to be used or created under the destination '
                                   'git repository, this sub directory will be used to hold the test result files. '
                                   'Use sub directory if need a custom directory to hold test files.')
    parser_build.add_argument('-o', '--overwrite_result', action='store_true',
                              help='(Optional) To overwrite existing testresult file with new file provided.')
