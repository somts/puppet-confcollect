# THIS FILE MANANGED BY PUPPET.
''' git_check_add_commit_pull_push.py

    Open up a git repository based on supplied command-line argument.
    If the repository has any changes or new files, add/commit them,
    then pull from our origin (rebasing) and finally push changes to
    the origin.
'''
import logging
from os import path
from socket import gethostname
from time import gmtime, strftime
from getpass import getuser
from git import Repo

def git_check_add_commit_pull_push(git_dir, logger):
    '''Check git repo for changes, and then blindly
    commit/push if changes are found.'''

    msg = '%s@%s:%s, %s update at %s' % (
        getuser(),
        gethostname(),
        git_dir,
        path.basename(__file__),
        strftime("%Y-%m-%d %H:%M:%S %Z", gmtime())
        )

    with Repo(git_dir) as repo:
        git = repo.git

        if git.status('--porcelain').__len__() == 0:
            logger.info('No repo changes. End.')
        else:
            logger.info('Repo changed...')
            logger.info('Committing changes with message "%s"...', msg)
            git.add('-A')
            git.commit('-a', '-m', msg)
            logger.info('Changes committed...')
            git.pull('--rebase')
            git.push()
            logger.info('Changes pushed to origin.')
