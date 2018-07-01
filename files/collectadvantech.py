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

    # Different firmwares have different functions...
    url1 = "http://%s:%i/cgi-bin/result.cgi?types=export" % (host, port)
    url2 = "http://%s:%i/cgi-bin/index.cgi?func=doexport" % (host, port)

    url = url1

    logger = setup_logger('collectadvantech_%s' % host,
                          path.join(log_dir, 'collectadvantech.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)
    logger.debug('Attempting to talk to %s ...', url1)

    if username is None and password is None:
        # Out of the box, there seems to be no password Advantechs
        response = requests.get(url1)
        if response.status_code == 404:
            logger.debug('Done talking to %s.', url)
            logger.debug('Attempting to talk to %s ...', url2)
            response = requests.get(url2)
            url = url2
    else:
        logger.warn('username/password unsupported for collectadvnatech')

    logger.debug('Done talking to %s.', url)

    # Write data to disk
    fname = path.join(destination_dir, host + '.conf')
    logger.debug('Opening %s for writing conf data...', fname)
    myfile = open(fname, 'w')
    # We must write as UTF-8 to avoide errors like:
    # UnicodeEncodeError: 'ascii' codec can't encode character u'\x84'
    # in position 2594: ordinal not in range(128)
    # ...from the Healy CLAB1/CLAB2 devices.  Not sure why.
    myfile.write(response.text.encode('utf-8'))
    myfile.close()

    logger.debug('conf data saved to %s.', fname)
    logger.info('END %s', host)
#pylint: enable=too-many-arguments
