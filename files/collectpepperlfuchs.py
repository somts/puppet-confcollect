# THIS FILE MANANGED BY PUPPET.
''' collectpepperlfuchs.py

    Pepper L Fuchs config grabber. Used to keep Pepper L Fuchs config
    file(s) up-to-date from various locations.'''

from os import path
from pathlib import Path
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
              hostname=None,
              local_filename=None,
              ):
    '''Login to Pepper L Fuchs (P+F) and return conf data'''

    # host and hostname are the same thing unless overridden
    hostname = host if hostname is None else hostname

    logger = setup_logger(f'collectpepperlfuchs{hostname}',
                          path.join(log_dir,
                                    f'collectpepperlfuchs.{hostname}.log'),
                          level=loglevel)
    logger.info('BEGIN %s', host)

    # Different firmwares have different functions...
    url = f'{protocol}://{host}:{port}/goforms/ConfigGet'

    destp = Path(destination_dir).absolute()
    if local_filename is None:
        local_filename = destp.joinpath('%s.%s' % (
            hostname.split('.')[0], extension))
    else:
        # ignore destination_dir when local_filename is provided
        # ... unless local_filename is relative
        if not Path(local_filename).is_absolute():
            local_filename = destp.joinpath(local_filename)

        destp = Path(local_filename).parent()

    response = None

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
        try:  # Attempt to ensure dir exists
            destp.mkdir(parents=True, exist_ok=True)
        except (FileNotFoundError, PermissionError) as err:
            logger.error('Error with target dir %s: %s', destp, err)
        except Exception as err:
            logger.error('Unexpected error with target dir %s: %s', destp, err)

        logger.debug('Opening %s for writing conf data...', local_filename)

        # We must write as UTF-8 to avoid errors like:
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\x84'
        # in position 2594: ordinal not in range(128)
        # ...from the Healy CLAB1/CLAB2 devices.  Not sure why.
        with open(local_filename, 'wb') as myfile:
            myfile.write(response.text.encode('utf-8'))

        logger.debug('ds data saved to %s.', local_filename)

    logger.info('END %s', host)
