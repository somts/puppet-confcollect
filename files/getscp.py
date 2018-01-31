#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getscp.py

    Config grabber via Netmiko/SCP. Used to keep various
    SSH/SCP-capable config file(s) up-to-date from various locations.'''

import logging
import multiprocessing
from ConfigParser import RawConfigParser, NoOptionError
from argparse import ArgumentParser
from getpass import getuser
from os import path
from subprocess import check_output
from netmiko import ConnectHandler, SCPConn
from netmiko.ssh_exception import NetMikoTimeoutException

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
        path.dirname(path.dirname(__file__)), 'etc', 'getscp.ini'))

    conf = RawConfigParser()
    conf.read(myini)
    return conf

def cfgworker(host, loglevel,
              device_type='cisco_ios',
              username='admin',
              password='!!',
              destination_dir='/tmp',
              remote_filename='nvram:startup-config',
              logdir='/tmp',
              filename_extension='cfg'
             ):
    '''Multiprocessing worker for get_cfg()'''

    logging.basicConfig(
        filename=path.join(logdir, 'getscp.%s.log' % host),
        format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        level=loglevel,
    )

    logging.info('BEGIN %s', host)

    local_filename = path.join(path.realpath(destination_dir),
                               '%s.%s' % (host.split('.')[0],
                                          filename_extension))

    try:
        net_connect = ConnectHandler(ip=host,
                                     device_type=device_type,
                                     username=username,
                                     password=password)

        net_connect.enable()
        scp_conn = SCPConn(net_connect)
        scp_conn.scp_get_file(remote_filename, local_filename)
        logging.info('Configuration for %s transferred successfully.', host)
        scp_conn.close()

    except NetMikoTimeoutException as err:
        logging.error('Error with %s: %s', host, err)

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

        try:
            extension = config.get(host, 'extension')
        except NoOptionError:
            extension = 'cfg'

        # Set up structured data for worker_wrapper()
        jobs.append(((host, loglevel), {
            'device_type': config.get(host, 'device_type'),
            'username': config.get(host, 'username'),
            'password': config.get(host, 'password'),
            'destination_dir': config.get(host, 'destination_dir'),
            'filename_extension': extension,
            'remote_filename': config.get(host, 'remote_filename'),
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
         conf.get('main', 'repo_dir')])

if __name__ == '__main__':
    main()
