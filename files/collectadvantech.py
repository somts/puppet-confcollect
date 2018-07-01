# THIS FILE MANANGED BY PUPPET.
''' collectadvantech.py

    Advantech config grabber. Used to keep Advantech config file(s)
    up-to-date from various locations.'''

from os import path
import requests

from somtsfilelog import setup_logger

#pylint: disable=too-many-arguments
def cfgworker(host, loglevel,
              port=80,
              username=None,
              password=None,
              destination_dir='/tmp',
              log_dir='/tmp',
             ):
    '''Login to Advantech and return conf data'''

    url = "http://%s:%i/cgi-bin/result.cgi?types=export" % (host, port)

    logger = setup_logger('collectadvantech_%s' % host,
                          path.join(log_dir, 'collectadvantech.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)
    logger.debug('Attempting to talk to %s ...', url)

    if username is None and password is None:
        # Out of the box, there seems to be no password Advantechs
        response = requests.get(url)
    else:
        logger.warn('username/password unsupported for collectadvnatech')

    logger.debug('Done talking to %s.', url)

    # Write data to disk
    fname = path.join(destination_dir, host + '.conf')
    logger.debug('Opening %s for writing conf data...', fname)
    myfile = open(fname, 'w')
    myfile.write(response.text)
    myfile.close()

    logger.debug('conf data saved to %s.', fname)
    logger.info('END %s', host)
#pylint: enable=too-many-arguments
