# THIS FILE MANANGED BY PUPPET.
''' collectmediacento.py

    Config grabber via Telnetlib. Used to keep BlackBox MediaCento
    config file(s) up-to-date from various locations.'''

import socket
from os import path
from telnetlib import Telnet

from somtsfilelog import setup_logger


def cfgworker(host, loglevel,
              port=24,
              username='root',
              destination_dir='/tmp',
              remote_cmd='astparam dump',
              log_dir='/tmp',
              filename_extension='astparam',
              timeout=20,
              local_filename=None
              ):
    '''Speak to a Black Box MediaCento device using telnet on TCP/24
    (not TCP/23), and run `astparam dump` to get its config. Security on
    these things are terrible; username is root and there is no password.
    Hopefully for you, this function is executed on an isolated LAN.

    For details on astparam settings, see
    support.justaddpower.com/kb/article/30-device-settings-via-the-command-line
    '''

    logger = setup_logger('collectmediacento_%s' % host,
                          path.join(log_dir, 'collectmediacento.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)

    if local_filename is None:
        local_filename = path.join(path.realpath(destination_dir),
                                   '%s.%s' % (host.split('.')[0],
                                              filename_extension))
    try:
        tel = Telnet(host, port)

        tel.read_until('login: '.encode('utf-8'), timeout)
        cmd = "%s\n" % username
        tel.write(cmd.encode('utf-8'))

        tel.read_until('#'.encode('utf-8'), timeout)

        # Get the current config
        cmd = "%s\n" % remote_cmd
        tel.write(cmd.encode('utf-8'))
        astparams = tel.read_until('#'.encode('utf-8'), timeout).decode()
        logger.info('hi')

        # Close telnet session.
        tel.close()

        # Write data, eliminating:
        # 1) The 0th line -- this is the command we issued
        # 2) The last line -- this is the command prompt we waited for
        with open(local_filename, 'w') as filepointer:
            filepointer.write("\n".join(astparams.splitlines()[1:-1]))

        logger.info('%s saved to disk', local_filename)

    except socket.error as err:
        logger.error('Error with %s: %s', host, err)
        return
    except Exception as err:
        logger.error('Unexpected error with %s: %s', host, err)
        return

    logger.info('END %s', host)
