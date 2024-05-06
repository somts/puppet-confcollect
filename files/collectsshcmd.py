# THIS FILE MANANGED BY PUPPET.
''' collectsshcmd.py

    Login via ssh and record the output of command(s)'''
from os import path, rename
from tempfile import NamedTemporaryFile
from socket import gethostbyname, gethostname
from getpass import getuser
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

from somtsfilelog import setup_logger


def cfgworker(host, loglevel,
              device_type='generic_termserver',
              username='admin',
              password='!!',
              destination_dir='staging',
              commands=['date'],
              log_dir='/tmp',
              filename_extension='txt',
              dest_filename=None,
              dest_username=None,
              dest_password=None,
              dest_host=None
              ):
    '''Multiprocessing worker for collectsshcmd'''

    logger = setup_logger('collectsshcmd_%s' % host,
                          path.join(log_dir, 'collectsshcmd.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)

    if dest_username is None:
        dest_username = getuser()

    if dest_host is None:
        dest_host = gethostbyname(gethostname())

    if dest_filename is None:
        dest_filename = path.join(path.realpath(destination_dir),
                                  '%s.%s' % (host.split('.')[0],
                                             filename_extension))

    try:
        logger.debug('Attempt to connect to host %s, device type %s',
                     host, device_type)

        # Open up a temporary file to write to. Don't want to overwite
        # partial sessions onto the production file
        with NamedTemporaryFile(delete=False) as filep:
            logger.debug('Opened %s for caching.', filep.name)

            # Connect to our device
            with ConnectHandler(host=host,
                                device_type=device_type,
                                username=username,
                                password=password) as net_connect:
                logger.debug('Connecting to %s.', host)
                net_connect.enable()

                # Execute all commands
                for command in commands:
                    logger.debug('Sending command, "%s"...', command)
                    out = net_connect.send_command(command)
                    logger.debug(out)
                    filep.write(str.encode(f"# {command}\n{out}\n\n"))
                    del out
            filep.close()

            # Operations done, move file into place
            logger.info('Moving %s to %s.', filep.name, dest_filename)
            rename(filep.name, dest_filename)

    except NetMikoTimeoutException as err:
        logger.error('Error with %s: %s', host, err)
    except Exception as err:
        logger.error('Unexpected error with %s: %s', host, err)

    logger.info('END %s', host)
