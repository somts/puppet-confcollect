#!/usr/bin/env python

# THIS FILE MANANGED BY PUPPET.
''' getpfsense.py
   pfSense config grabber. Used to keep pfSense XML config file(s)
   up-to-date from various locations. See
   https://doc.pfsense.org/index.php/Remote_Config_Backup#2.3.3_and_Later
   for details. Note that we make subprocess calls to wget to minimize
   translation from the pfSense docs.'''

import tempfile
import os
import subprocess
import ConfigParser
from urllib import urlencode

def get_args():
    '''Read config'''
    myini = os.path.realpath(os.path.join(
        os.path.realpath(os.path.dirname(os.path.dirname(__file__))),
        'etc/getpfsense.ini'))

    conf = ConfigParser.RawConfigParser()
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
    except ConfigParser.NoOptionError:
        wget_tries = 3

    try:
        wget_timeout = config.get('main', 'wget_timeout')
    except ConfigParser.NoOptionError:
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

        # Open cookie file
        with tempfile.NamedTemporaryFile() as cookie:

            # Step 1:
            # Fetch the login form and save the cookies and CSRF token
            wget = base_wget + ['--save-cookies=%s' % cookie.name, url]
            proc = subprocess.Popen(wget, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            csrf1 = get_csrf_magic(proc.communicate()[0])

            # Step 2:
            # Submit the login form along with the first CSRF token and
            # save the second CSRF token -- now the script is logged in
            # and can take action.
            wget = base_wget + [
                '--load-cookies=%s' % cookie.name,
                '--save-cookies=%s' % cookie.name,
                '--post-data',
                urlencode({
                    'login': 'Login',
                    'usernamefld': config.get(host, 'username'),
                    'passwordfld': config.get(host, 'password'),
                    '__csrf_magic': csrf1,
                    }),
                url]

            proc = subprocess.Popen(wget, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            csrf2 = get_csrf_magic(proc.communicate()[0])

            # Step 3:
            # Submit the download form along with the second CSRF token
            # to save a copy of config.xml
            wget = base_wget + [
                '--load-cookies=%s' % cookie.name,
                '--post-data',
                urlencode({
                    'download': 'download',
                    'donotbackuprrd': 'yes',
                    '__csrf_magic': csrf2,
                    }),
                url]

            proc = subprocess.Popen(wget, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            myxml = proc.communicate()[0]

        # Write XML to disk
        try:
            destdir = config.get(host, 'destination_dir')
        except ConfigParser.NoOptionError:
            destdir = config.get('main', 'destination_dir')

        myfile = open(os.path.join(destdir, host + '.xml'), 'w')
        myfile.write(myxml)
        myfile.close()

def main():
    '''Main process'''
    conf = get_args()
    xml = wget_xml(conf)

if __name__ == '__main__':
    main()
