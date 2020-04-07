# THIS FILE MANANGED BY PUPPET.
''' collectpeplink.py

    Config grabber via requests. Used to keep Peplink config file(s)
    up-to-date from various locations. Peplink conf files change with
    each download, so we add an intentional delay interval to mitigate'''
import time
import os
import stat
import requests

from somtsfilelog import setup_logger

#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals
def cfgworker(host, loglevel,
              port=443,
              username='admin',
              password='!!',
              destination_dir='/tmp',
              log_dir='/tmp',
              filename_extension='conf',
              timeout=60,
              delay_days=90,
              local_filename=None
             ):
    '''Speak to a Peplink WUI using requests on TCP/443'''

    logger = setup_logger('collectpeplink_%s' % host,
                          os.path.join(log_dir, 'collectpeplink.%s.log' % host),
                          level=loglevel)

    if local_filename is None:
        local_filename = os.path.join(os.path.realpath(destination_dir),
                                      '%s.%s' % (host.split('.')[0],
                                                 filename_extension))
    # Build URL and POST data
    baseurl = 'https://%s:%i/cgi-bin/MANGA/' % (host, port)
    postdata = {'func': 'login', 'username': username, 'password': password}

    logger.info('BEGIN %s', host)

    # assess file modification time, if any
    if os.path.isfile(local_filename):
        mdays = (time.time() - os.stat(local_filename)[stat.ST_MTIME])/86400.
    else:
        mdays = 0

    # Do nothing if our config has been collected "recently enough"
    if delay_days > mdays:
        logger.info('%s was modified ' % local_filename + \
                    '%i days ago, which is more recently than ' % mdays + \
                    'delay_days value of %i. Doing nothing' % delay_days)

    # Collect config and save to our repo
    else:
        try:
            with requests.Session() as session:
                session.timeout = timeout
                session.verify = False # complain about,but ignore cert errors
                login = session.post(baseurl + 'api.cgi', data=postdata)
                if login.status_code == 200:
                    config = session.get(baseurl + 'download_config.cgi')

                    # Response is a binary blob. Write binary .conf file
                    with open(local_filename, 'wb') as filepointer:
                        filepointer.write(config.content)

            logger.info('%s saved to disk', local_filename)

        #pylint: disable-msg=broad-except
        except Exception as err:
            logger.error('Unexpected error with %s: %s', host, err)
            return
        #pylint: enable-msg=broad-except

    logger.info('END %s', host)
#pylint: enable=too-many-locals
#pylint: enable=too-many-arguments
