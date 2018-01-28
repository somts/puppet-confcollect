#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getscp.py

    Config grabber via Netmiko/SCP. Used to keep various
    SSH/SCP-capable config file(s) up-to-date from various locations.'''

import logging
import os
from ConfigParser import RawConfigParser
from argparse import ArgumentParser
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
    myini = os.path.realpath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'etc/getscp.ini'))

    conf = RawConfigParser()
    conf.read(myini)
    return conf

def get_conf_via_scp(ssh_conn, router, destination_dir,
                     remote_filename='nvram:startup-config'):
    '''Copy a remote file to a local file'''

    local_filename = os.path.join(os.path.realpath(destination_dir),
                                  '%s.cfg' % router)
    scp_conn = SCPConn(ssh_conn)
    scp_conn.scp_get_file(remote_filename, local_filename)
    logging.info('Configuration for %s transferred successfully.', router)
    scp_conn.close()

def get_cfg(config):
    '''Login to a device with netmiko and copy data to our repo.'''

    # Start fetching all supported configs...
    for host in config.sections():

        # Skip main section
        if host == 'main':
            continue

        logging.debug('BEGIN %s', host)

        try:
            net_connect = ConnectHandler(ip=host,
                                         device_type=config.get(host,
                                                                'device_type'),
                                         username=config.get(host, 'username'),
                                         password=config.get(host, 'password'))

            net_connect.enable()
            get_conf_via_scp(net_connect,
                             host,
                             config.get(host, 'destination_dir'),
                             remote_filename=config.get(host,
                                                        'remote_filename'))

        except NetMikoTimeoutException as err:
            logging.error('Error with %s: %s', host, err)
            continue

        logging.debug('END %s', host)

    # Commit any changes
    logging.debug('Committing changes, if any, to our git repo, %s.',
                  config.get('main', 'repo_dir'))

    check_output(
        [os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      'git_commit_push.py'),
         '-D',
         config.get('main', 'repo_dir')])

def main():
    '''Main process'''
    args = get_arguments()
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format='[%(levelname)s] %(asctime)s %(lineno)d %(message)s',
                        level=level)
    conf = read_ini()
    get_cfg(conf)

if __name__ == '__main__':
    main()
