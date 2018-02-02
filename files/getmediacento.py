#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getmediacento.py

    Config grabber via Telnetlib. Used to keep BlackBox MediaCento
    config file(s) up-to-date from various locations.'''

import logging
import multiprocessing
from ConfigParser import RawConfigParser
from argparse import ArgumentParser
from getpass import getuser
from os import path
from subprocess import check_output
from telnetlib import Telnet

def get_arguments():
    '''Get/set command-line options'''

    parser = ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', help='Turn on debugging output.')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
                        help="No console output (for running from cron)")

    return parser.parse_args()

def read_ini():
    '''Read .ini config'''
    myini = path.realpath(path.join(
        path.dirname(path.dirname(__file__)), 'etc', 'getmediacento.ini'))

    conf = RawConfigParser()
    conf.read(myini)
    return conf

def cfgworker(host, loglevel,
              port=24,
              username='root',
              destination_dir='/tmp',
              remote_cmd='astparam dump',
              logdir='/tmp',
              filename_extension='astparam',
              timeout=20
             ):
    '''Speak to a Black Box MediaCento device using telnet on TCP/24
    (not TCP/23), and run `astparam dump` to get its config. Security on
    these things are terrible; username is root and there is no password.
    Hopefully for you, this function is executed on an isolated LAN.

    For details on astparam settings, see
    support.justaddpower.com/kb/article/30-device-settings-via-the-command-line
    '''

    logging.basicConfig(
        filename=path.join(logdir, 'getmediacento.%s.log' % host),
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        level=loglevel,
    )

    logging.info('BEGIN %s', host)

    local_filename = path.join(path.realpath(destination_dir),
                               '%s.%s' % (host.split('.')[0],
                                          filename_extension))
    try:
        tel = Telnet(host, port)

        tel.read_until('login: ', timeout)
        tel.write("%s\n" % username)

        tel.read_until('#', timeout)

        # Get the current config
        tel.write("%s\n" % remote_cmd)
        myast = tel.read_until('#', timeout)

        # Close telnet session.
        tel.close()

        # Write data, eliminating:
        # 1) The 0th line -- this is the command we issued
        # 2) The last line -- this is the command prompt we waited for
        with open(local_filename, 'w') as filepointer:
            filepointer.write("\n".join(myast.split("\n")[1:-1]))

        logging.info('%s saved to disk', local_filename)

    except Exception, err:
        logging.error('%s had issues %s.', host, err)
        return

    logging.info('END %s', host)

def worker_wrapper(arg):
    '''Take structured data and turn it into args and/or kwargs for cfgworker()'''
    args, kwargs = arg
    return cfgworker(*args, **kwargs)

def main():
    '''Main process'''
    config = read_ini()
    args = get_arguments()

    if args.quiet:
        loglevel = logging.ERROR
    elif args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    logdir = path.join('/var', 'log', getuser())

    pool_size = multiprocessing.cpu_count() * 4
    pool = multiprocessing.Pool(processes=pool_size)

    # Build jobs
    jobs = []
    for host in config.sections():

        # Skip main section
        if host == 'main':
            continue

        # Set up structured data for worker_wrapper()
        jobs.append(((host, loglevel), {
            'destination_dir': config.get(host, 'destination_dir'),
            'logdir': logdir,
            }))

    # Start fetching all supported configs...
    pool.map(worker_wrapper, jobs)
    pool.close() # no more tasks
    pool.join()  # wrap up current tasks

    # Commit any changes
    check_output(
        [path.join(path.dirname(path.realpath(__file__)), 'git_commit_push.py'),
         '-D',
         config.get('main', 'repo_dir')])

if __name__ == '__main__':
    main()
