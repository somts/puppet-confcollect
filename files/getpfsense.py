#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getpfsense.py

    pfSense config grabber. Used to keep pfSense XML config file(s)
    up-to-date from various locations. See
    https://doc.pfsense.org/index.php/Remote_Config_Backup#2.3.3_and_Later
    for details. Note that we make subprocess calls to wget to minimize
    translation from the pfSense docs.'''

import logging
import tempfile
import os
from argparse import ArgumentParser
from ConfigParser import RawConfigParser, NoOptionError
from subprocess import check_output, CalledProcessError
from urllib import urlencode

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
        os.path.dirname(os.path.dirname(__file__)), 'etc/getpfsense.ini'))

    conf = RawConfigParser()
    conf.read(myini)
    return conf

def get_csrf_magic(mystr):
    '''Take a string of pfSense WUI data and extract the CSRF token'''
    objects = mystr.split()
    for index, obj in enumerate(objects):
        if obj == "name='__csrf_magic'":
            # get next var
            csrf = objects[index + 1]

            # return the string between quotes
            return csrf[csrf.find('"')+1:-1]

def wget_xml(config):
    '''Login to pfSense with wget and return XML data'''

    try:
        wget_tries = config.get('main', 'wget_tries')
    except NoOptionError:
        wget_tries = 3

    try:
        wget_timeout = config.get('main', 'wget_timeout')
    except NoOptionError:
        wget_timeout = 300

    base_wget = [
        '/usr/bin/wget',
        '--no-check-certificate',
        '--keep-session-cookies',
        '--tries', '%s' % wget_tries,
        '--timeout', '%s' % wget_timeout,
        '-qO-']

    # Start fetching all supported pfSense configs...
    for host in config.sections():

        # Skip main section
        if host == 'main':
            continue

        # Set up variables
        url = "https://%s/diag_backup.php" % host

        logging.debug('Attempting to talk to %s ...', url)

        # Open cookie file
        with tempfile.NamedTemporaryFile() as cookie:

            # Step 1:
            # Fetch the login form and save the cookies and CSRF token
            try:
                csrf1 = get_csrf_magic(check_output(
                    base_wget + ['--save-cookies=%s' % cookie.name, url]))
            except CalledProcessError:
                logging.error('Could not collect CSRF magic #1 from %s', url)
                continue

            # Step 2:
            # Submit the login form along with the first CSRF token and
            # save the second CSRF token -- now the script is logged in
            # and can take action.
            try:
                csrf2 = get_csrf_magic(check_output(
                    base_wget + [
                        '--load-cookies=%s' % cookie.name,
                        '--save-cookies=%s' % cookie.name,
                        '--post-data',
                        urlencode({
                            'login': 'Login',
                            'usernamefld': config.get(host, 'username'),
                            'passwordfld': config.get(host, 'password'),
                            '__csrf_magic': csrf1,
                            }),
                        url]))
            except CalledProcessError:
                logging.error('Could not collect CSRF magic #2 from %s', url)
                continue

            # Step 3:
            # Submit the download form along with the second CSRF token
            # to save a copy of config.xml
            try:
                myxml = check_output(
                    base_wget + [
                        '--load-cookies=%s' % cookie.name,
                        '--post-data',
                        urlencode({
                            'download': 'download',
                            'donotbackuprrd': 'yes',
                            '__csrf_magic': csrf2,
                            }),
                        url])
            except CalledProcessError:
                logging.error('Could not collect XML from %s', url)
                continue

        # Write XML to disk
        try:
            destdir = config.get(host, 'destination_dir')
        except NoOptionError:
            destdir = config.get('main', 'destination_dir')

        myfile = open(os.path.join(destdir, host + '.xml'), 'w')
        myfile.write(myxml)
        myfile.close()

        logging.debug('Done talking to %s, XML saved.', url)

    # Commit any changes
    logging.debug('Committing changes, if any, to our git repo.')

    check_output(
        [os.path.join(os.path.dirname(os.path.realpath(__file__)),
                      'git_commit_push.py'),
         '-D',
         os.path.dirname(config.get('main', 'destination_dir'))])

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
    wget_xml(conf)

if __name__ == '__main__':
    main()
