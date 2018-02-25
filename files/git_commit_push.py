#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' git_commit_push.py

    Open up a git repository based on supplied command-line argument.
    If the repository has any changes or new files, add/commit them,
    then pull from our origin (rebasing) and finally push changes to
    the origin.
'''
import logging
import os
from argparse import ArgumentParser
from socket import gethostname
from time import gmtime, strftime
from types import StringType
from git import Repo

def get_arguments():
    '''Get/set command-line options'''

    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', help='Turn on debugging output.')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help="No console output (for running from cron)")
    parser.add_argument('-D', '--git-dir',
                        action='store',
                        required=True,
                        dest='git_dir',
                        type=StringType,
                        help='directory where our git repo resides')

    return parser.parse_args()

def main():
    '''Main process. Check git repo for changes, and then blindly
    commit/push if changes are found.'''

    args = get_arguments()
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format='[%(levelname)s] %(asctime)s %(lineno)d %(message)s',
                        level=level)

    msg = 'confcollect %s update from %s @ %s' % (
        os.path.basename(__file__),
        gethostname(),
        strftime("%Y-%m-%d %H:%M:%S %Z", gmtime()))

    logging.debug('Opening git repo at args.git_dir')
    repo = Repo(args.git_dir)
    git = repo.git

    if git.status('--porcelain').__len__() != 0:
        logging.info('Repo changed. Committing changes with message "%s"', msg)
        git.add('-A')
        git.commit('-a', '-m', msg)
        git.pull('--rebase')
        git.push()
    else:
        logging.info('No repo changes. End.')

if __name__ == '__main__':
    main()

