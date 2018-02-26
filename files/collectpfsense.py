# THIS FILE MANANGED BY PUPPET.
''' collectpfsense.py

    pfSense config grabber. Used to keep pfSense XML config file(s)
    up-to-date from various locations. See
    https://doc.pfsense.org/index.php/Remote_Config_Backup#2.3.3_and_Later
    for details. Note that we make subprocess calls to wget to minimize
    translation from the pfSense docs.'''

from os import path
from subprocess import check_output, CalledProcessError
from tempfile import NamedTemporaryFile
from urllib import urlencode

from somtsfilelog import setup_logger

def get_csrf_magic(mystr):
    '''Take a string of pfSense WUI data and extract the CSRF token'''
    objects = mystr.split()
    for index, obj in enumerate(objects):
        if obj == "name='__csrf_magic'":
            # get next var
            csrf = objects[index + 1]

            # return the string between quotes
            return csrf[csrf.find('"')+1:-1]

#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals
def cfgworker(host, loglevel,
              port=443,
              username='admin',
              password='!!',
              destination_dir='/tmp',
              log_dir='/tmp',
              tries=3,
              timeout=300
             ):
    '''Login to pfSense with wget and return XML data'''

    # Skip DEFAULT/main section
    if host == 'DEFAULT':
        return
    elif host == 'main':
        return

    # Set up variables
    url = "https://%s:%i/diag_backup.php" % (host, port)
    base_wget = [
        '/usr/bin/wget',
        '--no-check-certificate',
        '--keep-session-cookies',
        '--tries', '%s' % tries,
        '--timeout', '%s' % timeout,
        '-qO-']

    logger = setup_logger('collectpfsense_%s' % host,
                          path.join(log_dir, 'collectpfsense.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)
    logger.debug('Attempting to talk to %s ...', url)

    # Open cookie file
    with NamedTemporaryFile() as cookie:

        # Step 1:
        # Fetch the login form and save the cookies and CSRF token
        try:
            csrf1 = get_csrf_magic(check_output(
                base_wget + ['--save-cookies=%s' % cookie.name, url]))
            logger.debug('Collected csrf1, "%s" ...', csrf1)
        except CalledProcessError:
            logger.error('Could not collect CSRF magic #1 from %s', url)
            return

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
                        'usernamefld': username,
                        'passwordfld': password,
                        '__csrf_magic': csrf1,
                        }),
                    url]))
            logger.debug('Collected csrf2, "%s" ...', csrf2)
        except CalledProcessError:
            logger.error('Could not collect CSRF magic #2 from %s', url)
            return

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
            logger.debug('Collected XML data.')
        except CalledProcessError:
            logger.error('Could not collect XML from %s', url)
            return
    logger.debug('Done talking to %s.' % url)

    # Write XML to disk
    fname = path.join(destination_dir, host + '.xml')
    logger.debug('Opening %s for writing XML data...' % fname)
    myfile = open(fname, 'w')
    myfile.write(myxml)
    myfile.close()

    logger.debug('XML data saved to %s.', fname)
    logger.info('END %s', host)
#pylint: enable=too-many-arguments
#pylint: enable=too-many-locals
