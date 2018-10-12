# test case management tool - store test result & log to git repository
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
from oe.path import copytree

class GitStore(object):

    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.base_path = self.script_path + '/../../..'

    def _get_top_dir_to_sub_dirs_path(self, top_dir, sub_dir_list):
        for sub_dir in sub_dir_list:
            top_dir = os.path.join(top_dir, sub_dir)
        return top_dir

    def _get_full_path_to_top_and_sub_dir(self, dir, top_dir, sub_dir_list):
        full_path_dir = os.path.join(dir, top_dir)
        full_path_dir = self._get_top_dir_to_sub_dirs_path(full_path_dir, sub_dir_list)
        return full_path_dir

    def _check_if_dir_contain_top_dir_and_sub_dirs(self, dir, top_dir, sub_dir_list):
        dest_dir = self._get_full_path_to_top_and_sub_dir(dir, top_dir, sub_dir_list)
        if os.path.exists(dest_dir):
            return True
        else:
            return False

    def _git_init(self, git_repo):
        try:
            repo = GitRepo(git_repo, is_topdir=True)
        except GitError:
            print("Non-empty directory that is not a Git repository "
                   "at {}\nPlease specify an existing Git repository, "
                   "an empty directory or a non-existing directory "
                   "path.".format(git_repo))
        return repo

    def _run_git_cmd(self, repo, cmd):
        try:
            output = repo.run_cmd(cmd)
            return True, output
        except GitError:
            return False, None

    def _check_if_git_repo_and_git_branch_exist(self, git_repo, git_branch):
        git_dir = '%s/.git' % git_repo
        if not os.path.exists(git_dir):
            return False
        repo = self._git_init(git_repo)
        status, output = self._git_checkout_git_repo(repo, git_branch)
        return status

    def _git_checkout_git_repo(self, repo, git_branch):
        cmd = 'checkout %s' % git_branch
        return self._run_git_cmd(repo, cmd)

    def _create_temporary_workspace_dir(self):
        return tempfile.mkdtemp(prefix='testresultlog.')

    def _remove_temporary_workspace_dir(self, workspace_dir):
        return subprocess.run(["rm", "-rf",  workspace_dir])

    def _make_directories(self, logger, full_path_dir):
        logger.debug('Creating directories: %s' % full_path_dir)
        pathlib.Path(full_path_dir).mkdir(parents=True, exist_ok=True)

    def _copy_files_from_source_to_destination_dir(self, logger, source_dir, destination_dir):
        if os.path.exists(source_dir) and os.path.exists(destination_dir):
            logger.debug('Copying test result & log from %s to %s' % (source_dir, destination_dir))
            copytree(source_dir, destination_dir)

    def _push_testsuite_testcase_json_file_to_git_repo(self, logger, file_dir, git_repo, git_branch, top_dir, sub_dir_list):
        logger.debug('Storing test result & log inside git repository (%s) and branch (%s)'
                     % (git_repo, git_branch))
        top_and_sub_dir = self._get_top_dir_to_sub_dirs_path(top_dir, sub_dir_list)
        commit_msg_subject = 'Store %s from {hostname}' % top_and_sub_dir
        commit_msg_body = 'top dir: %s\nsub dir list: %s\nhostname: {hostname}' % (top_dir, sub_dir_list)
        return subprocess.run(["oe-git-archive",
                               file_dir,
                               "-g", git_repo,
                               "-b", git_branch,
                               "--commit-msg-subject", commit_msg_subject,
                               "--commit-msg-body", commit_msg_body])

    def _store_test_result_from_empty_git(self, logger, source_dir, dest_git_dir, git_branch, top_dir, sub_dir_list):
        workspace_dir = self._create_temporary_workspace_dir()
        full_path_dir = self._get_full_path_to_top_and_sub_dir(workspace_dir, top_dir, sub_dir_list)
        self._make_directories(logger, full_path_dir)
        self._copy_files_from_source_to_destination_dir(logger, source_dir, full_path_dir)
        self._push_testsuite_testcase_json_file_to_git_repo(logger, workspace_dir, dest_git_dir, git_branch, top_dir, sub_dir_list)
        self._remove_temporary_workspace_dir(workspace_dir)

    def _store_test_result_from_existing_git(self, logger, source_dir, dest_git_dir, git_branch, top_dir, sub_dir_list):
        full_path_dir = self._get_full_path_to_top_and_sub_dir(dest_git_dir, top_dir, sub_dir_list)
        if not self._check_if_dir_contain_top_dir_and_sub_dirs(dest_git_dir, top_dir, sub_dir_list):
            self._make_directories(logger, full_path_dir)
        self._copy_files_from_source_to_destination_dir(logger, source_dir, full_path_dir)
        self._push_testsuite_testcase_json_file_to_git_repo(logger, dest_git_dir, dest_git_dir, git_branch, top_dir, sub_dir_list)

    def store_test_result(self, logger, source_dir, dest_git_dir, git_branch, top_folder, sub_folder_list, overwrite_testresult):
        logger.debug('Initialize storing of test result & log')
        if self._check_if_git_repo_and_git_branch_exist(dest_git_dir, git_branch):
            repo = self._git_init(dest_git_dir)
            self._git_checkout_git_repo(repo, git_branch)
            logger.debug('Found destination git directory and git branch: %s %s' % (dest_git_dir, git_branch))
            if self._check_if_dir_contain_top_dir_and_sub_dirs(dest_git_dir, top_folder, sub_folder_list):
                logger.debug('Found existing top (%s) & sub (%s) directories inside: %s' %
                             (top_folder, sub_folder_list, dest_git_dir))
                if overwrite_testresult:
                    logger.debug('Removing and overwriting existing top (%s) & sub (%s) directories inside: %s' %
                                 (top_folder, sub_folder_list, dest_git_dir))
                    shutil.rmtree(os.path.join(dest_git_dir, top_folder))
                    self._store_test_result_from_existing_git(logger, source_dir, dest_git_dir, git_branch, top_folder,
                                                              sub_folder_list)
                else:
                    logger.debug('Skipped storing test result & log as it already exist. '
                                'Specify overwrite if you wish to delete existing testresult and store again.')
            else:
                logger.debug('Could not find top (%s) & sub (%s) directories inside: %s' %
                             (top_folder, sub_folder_list, dest_git_dir))
                self._store_test_result_from_existing_git(logger, source_dir, dest_git_dir, git_branch, top_folder,
                                                          sub_folder_list)
        else:
            logger.debug('Could not find destination git directory (%s) or git branch (%s)' % (dest_git_dir, git_branch))
            self._store_test_result_from_empty_git(logger, source_dir, dest_git_dir, git_branch, top_folder,
                                                   sub_folder_list)

    def checkout_git_branch(self, git_dir, git_branch):
        print('Checkout git branch ...')
        if self._check_if_git_repo_and_git_branch_exist(git_dir, git_branch):
            repo = self._git_init(git_dir)
            self._git_checkout_git_repo(repo, git_branch)
            return True
        else:
            print('Could not find git_dir or git_branch: %s %s' % (git_dir, git_branch))
            return False
