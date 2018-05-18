#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getconfs.py

    Config grabber master script. Used to keep various config file(s)
    up-to-date from various devices and locations.'''

import sys

from argparse import ArgumentParser
from getpass import getuser
from os import path
from logging import DEBUG
from logging import ERROR
from logging import INFO
from multiprocessing import Pool
from multiprocessing import cpu_count
from configparser import RawConfigParser, NoOptionError
from pprint import pformat

# Import custom libs from ../lib/python, relative to this file...
#pylint: disable=wrong-import-position
sys.path.append(path.join(path.dirname(path.dirname(path.abspath(__file__))),
                          'lib',
                          'python'))
import collectmediacento
import collectpfsense
import collectscp
import collectssh
from gitcheck import git_check_add_commit_pull_push
from somtsfilelog import setup_logger
#pylint: enable=wrong-import-position

def get_arguments():
    '''Get/set command-line options'''

    # Calculate some defaults

    # Most of the CPU time is spent waiting for remote hosts, so we can use
    # a fairly generous multiple of our CPUs ...
    pool_size = cpu_count() * 16
    log_dir = path.join('/var', 'log', getuser())
    ini = path.join(path.dirname(path.dirname(path.abspath(__file__))),
                    'etc', 'getconfs.ini')

    # Set up args
    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', help='Turn on debugging output.')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help="No console output (for running from cron)")
    parser.add_argument('-g', '--git', action='store_true',
                        dest='git', help='Turn on git check and commit.')
    parser.add_argument('-t', '--threads', action='store',
                        default=pool_size, dest='pool_size',
                        help='Number of threads. Default: %i.' % pool_size)
    parser.add_argument('-l', '--logdir', action='store', type=int,
                        default=log_dir, dest='log_dir',
                        help='Log dir to store logs in. Default: %s.' % log_dir)
    parser.add_argument('-i', '--ini', action='store',
                        dest='ini', default=ini,
                        help='.ini file to use for config. Default: %s' % ini)

    return parser.parse_args()

def worker_wrapper(arg):
    '''Take structured data and turn it into args and/or kwargs for a
    cfgworker().  By default, we assume this is an SCP daemon via
    Netmiko, but we also catch specialized cases too.'''
    args, kwargs = arg

    kwargs.pop('repo_dir', None) # remove repo_dir from kwargs

    if kwargs['device_type'] == 'mediacento':
        kwargs.pop('device_type', None) # remove device_type from kwargs
        return collectmediacento.cfgworker(*args, **kwargs)

    elif kwargs['device_type'] == 'pfsense':
        kwargs.pop('device_type', None) # remove device_type from kwargs
        return collectpfsense.cfgworker(*args, **kwargs)

    elif kwargs['device_type'] == 'cisco_s300': # No SCP on Cisco SG-300
        return collectssh.cfgworker(*args, **kwargs)

    # many device_type options for Netmiko SCP, so it is the default
    return collectscp.cfgworker(*args, **kwargs)

def main():
    '''Main process'''
    args = get_arguments()

    if args.quiet:
        loglevel = ERROR
    elif args.verbose:
        loglevel = DEBUG
    else:
        loglevel = INFO

    config = RawConfigParser()
    config.read(args.ini)

    logger = setup_logger('getconfs',
                          path.join(args.log_dir, 'getconfs.log'),
                          level=loglevel)

    # Build jobs
    repo_dirs = set()
    jobs = []
    for section in config.sections():

        section_dict = dict(config.items(section))

        # The module name can be the hostname, if present
        try:
            host = section_dict.pop('host')
        except KeyError:
            host = section

        # Set up structured data for worker_wrapper()
        jobs.append(((host, loglevel), section_dict))

        # Add any unique repo dirs to our set.
        try:
            repo_dirs.add(config.get(section, 'repo_dir'))
        except NoOptionError:
            pass

    logger.debug("Jobs built:\n%s", pformat(jobs))

    # Set up pools
    pool = Pool(processes=args.pool_size)

    # Start fetching all supported configs...
    logger.info('Processing %i jobs...', jobs.__len__())
    pool.map(worker_wrapper, jobs)
    pool.close() # no more tasks
    pool.join()  # wrap up current tasks
    logger.info('%i jobs processed.', jobs.__len__())

    # Commit any changes after we've attempted to collect everything
    for repo_dir in repo_dirs:
        if args.git:
            logger.info('Git checking enabled. Checking %s.', repo_dir)
            git_check_add_commit_pull_push(repo_dir, logger)
        else:
            logger.info('Git checks disabled. Will not process %s', repo_dir)

if __name__ == '__main__':
    main()
