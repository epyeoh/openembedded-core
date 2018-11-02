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
import subprocess
import shutil
import scriptpath
scriptpath.add_bitbake_lib_path()
scriptpath.add_oe_lib_path()
from oeqa.utils.git import GitRepo, GitError
from oe.path import copytree

class GitStore(object):

    def _check_if_dir_contain_sub_dir(self, dir, sub_dir):
        if os.path.exists(os.path.join(dir, sub_dir)):
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

    def _check_if_git_dir_exist(self, git_dir):
        if not os.path.exists('%s/.git' % git_dir):
            return False
        return True

    def _checkout_git_dir(self, git_dir, git_branch):
        repo = self._git_init(git_dir)
        cmd = 'checkout %s' % git_branch
        return self._run_git_cmd(repo, cmd)

    def _create_temporary_workspace_dir(self):
        return tempfile.mkdtemp(prefix='testresultlog.')

    def _remove_temporary_workspace_dir(self, workspace_dir):
        return subprocess.run(["rm", "-rf",  workspace_dir])

    def _make_directories(self, logger, target_dir):
        logger.debug('Creating directories: %s' % target_dir)
        bb.utils.mkdirhier(target_dir)

    def _copy_files_from_source_to_destination_dir(self, logger, source_dir, destination_dir):
        if os.path.exists(source_dir) and os.path.exists(destination_dir):
            logger.debug('Copying test result & log from %s to %s' % (source_dir, destination_dir))
            copytree(source_dir, destination_dir)

    def _push_testresult_files_to_git_repo(self, logger, file_dir, git_dir, git_branch, git_sub_dir):
        logger.debug('Storing test result & log inside git repository (%s) and branch (%s)'
                     % (git_dir, git_branch))
        commit_msg_subject = 'Store %s from {hostname}' % os.path.join(git_dir, git_sub_dir)
        commit_msg_body = 'git dir: %s\nsub dir list: %s\nhostname: {hostname}' % (git_dir, git_sub_dir)
        return subprocess.run(["oe-git-archive",
                               file_dir,
                               "-g", git_dir,
                               "-b", git_branch,
                               "--commit-msg-subject", commit_msg_subject,
                               "--commit-msg-body", commit_msg_body])

    def _store_test_result_from_empty_git(self, logger, source_dir, git_branch, git_dir, git_sub_dir):
        workspace_dir = self._create_temporary_workspace_dir()
        full_workspace_dir = os.path.join(workspace_dir, git_sub_dir)
        self._make_directories(logger, full_workspace_dir)
        self._copy_files_from_source_to_destination_dir(logger, source_dir, full_workspace_dir)
        self._push_testresult_files_to_git_repo(logger, workspace_dir, git_dir, git_branch, git_sub_dir)
        self._remove_temporary_workspace_dir(workspace_dir)

    def _store_test_result_from_existing_git(self, logger, source_dir, git_branch, git_dir, git_sub_dir):
        self._make_directories(logger, os.path.join(git_dir, git_sub_dir))
        self._copy_files_from_source_to_destination_dir(logger, source_dir, os.path.join(git_dir, git_sub_dir))
        self._push_testresult_files_to_git_repo(logger, git_dir, git_dir, git_branch, git_sub_dir)

    def store_test_result(self, logger, source_dir, git_branch, git_dir, git_sub_dir, overwrite_result):
        logger.debug('Initializing store the test result & log')
        if self._check_if_git_dir_exist(git_dir) and self._checkout_git_dir(git_dir, git_branch):
            logger.debug('Found destination git directory and git branch: %s %s' % (git_dir, git_branch))
            if self._check_if_dir_contain_sub_dir(git_dir, git_sub_dir):
                logger.debug('Found existing sub (%s) directory inside: %s' % (git_sub_dir, git_dir))
                if overwrite_result:
                    logger.debug('Overwriting existing testresult inside: %s' % (os.path.join(git_dir, git_sub_dir)))
                    shutil.rmtree(os.path.join(git_dir, git_sub_dir))
                    self._store_test_result_from_existing_git(logger, source_dir, git_branch, git_dir, git_sub_dir)
                else:
                    logger.debug('Skipped storing test result & log as it already exist. '
                                 'Specify overwrite if you wish to delete existing testresult and store again.')
            else:
                logger.debug('Could not find existing sub (%s) directories inside: %s' % (git_sub_dir, git_dir))
                self._store_test_result_from_existing_git(logger, source_dir, git_branch, git_dir, git_sub_dir)
        else:
            logger.debug('Could not find destination git directory (%s) or git branch (%s)' % (git_dir, git_branch))
            self._store_test_result_from_empty_git(logger, source_dir, git_branch, git_dir, git_sub_dir)

    def checkout_git_directory(self, logger, git_branch, git_dir):
        if self._check_if_git_dir_exist(git_dir):
            logger.debug('Checking out the provided git directory: %s (branch: %s)' % (git_dir, git_branch))
            return self._checkout_git_dir(git_dir, git_branch)
        else:
            logger.debug('Could not find the .git inside the provided directory %s' % git_dir)
            return False

