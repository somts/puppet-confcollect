# THIS FILE MANANGED BY PUPPET.
''' collectpepperlfuchs.py

    Pepper L Fuchs config grabber. Used to keep Pepper L Fuchs config
    file(s) up-to-date from various locations.'''

from os import path
import requests

from somtsfilelog import setup_logger


def cfgworker(host, loglevel,
              protocol='http',
              port=80,
              username=None,
              password=None,
              extension='ds',
              destination_dir='/tmp',
              log_dir='/tmp',
              ):
    '''Login to Pepper L Fuchs (P+F) and return conf data'''

    # Different firmwares have different functions...
    url = f"{protocol}://{host}:{port}/goforms/ConfigGet"

    response = None

    logger = setup_logger('collectpepperlfuchs%s' % host,
                          path.join(log_dir,
                                    f"collectpepperlfuchs.{host}.log"),
                          level=loglevel)
    logger.info('BEGIN %s', host)
    logger.debug('Attempting to talk to %s ...', url)

    if username is None and password is None:
        # Out of the box, there seems to be no password Pepper L Fuchs
        try:
            response = requests.get(url, timeout=(18.5, 90.5))

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError) as err:
            logger.info('Error with %s: "%s".', host, err)
        except Exception as err:
            logger.error('Unexpected error with %s: %s', host, err)
    else:
        logger.warning('username/password unsupported for collectpepperlfuchs')

    logger.debug('Done talking to %s.', url)

    if response is not None:
        # Write data to disk
        fname = path.join(destination_dir, f"dm_{host}.{extension}")
        logger.debug('Opening %s for writing conf data...', fname)

        # We must write as UTF-8 to avoid errors like:
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\x84'
        # in position 2594: ordinal not in range(128)
        # ...from the Healy CLAB1/CLAB2 devices.  Not sure why.
        with open(fname, 'wb') as myfile:
            myfile.write(response.text.encode('utf-8'))

        logger.debug('ds data saved to %s.', fname)

    logger.info('END %s', host)
