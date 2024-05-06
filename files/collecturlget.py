# THIS FILE MANANGED BY PUPPET.
''' collecturlget.py

    Advantech config grabber. Used to keep Advantech config file(s)
    up-to-date from various locations.'''
# pylint: disable=too-many-arguments
from os import path
import requests
from somtsfilelog import setup_logger


def cfgworker(host, loglevel,
              port=80,
              proto='http',
              urlpath='/',
              username=None,
              password=None,
              destination_dir='/tmp',
              log_dir='/tmp',
              extension='txt',
              ):
    '''Query a URL and return conf data'''

    if username is None:
        url = f"{proto}://{host}:{port}{path}"
    elif password is None:
        url = f"{proto}://{username}@{host}:{port}{path}"
    else:
        url = f"{proto}://{username}:{password}@{host}:{port}{path}"
    fname = path.join(destination_dir, host + '.' + extension)

    logger = setup_logger('collecturl_%s' % host,
                          path.join(log_dir, 'collecturl.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)
    logger.debug('Attempting to talk to %s ...', url)

    # pylint: disable-msg=broad-except
    try:
        with requests.get(url, timeout=(18.5, 90.5)) as response:
            logger.debug('Done talking to %s.', url)

            if response.ok is True:
                logger.debug('Opening %s for writing URL response data...',
                             fname)

                if response.apparent_encoding == 'ascii':
                    with open(fname, 'wb') as myfile:
                        myfile.write(response.text.encode('utf-8'))
                else:
                    with open(fname, 'wb') as myfile:
                        myfile.write(response.content)

                logger.debug('URL reponse data from &s saved to %s.',
                             url, fname)
            else:
                logger.debug('Response not OK')

    except requests.exceptions.RequestException as err:
        logger.info('Error with %s: "%s".', host, err)

    except Exception as err:
        logger.error('Unexpected error with %s: %s', host, err)
    # pylint: enable-msg=broad-except

    logger.info('END %s', host)
# pylint: enable=too-many-arguments
