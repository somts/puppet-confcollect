#!/usr/bin/env python
''' collectqflex.py
Talk to various devices, get their config and store.
'''
# Import python built-ins
import binascii
import csv
import os
import re
import tarfile
import socket
from tempfile import NamedTemporaryFile

# Import modules that tend to need a special install
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException
from paramiko.ssh_exception import SSHException

from somtsfilelog import setup_logger


def get_qflex_data(filecmddict, nm_kwargs, logger, enable=False, ending=None):
    '''Login to a Netmiko service, save output of a command.
       filecmddict is a dict: key = filename, value = command.
    '''

    hostinfo = '%s:%i (%s)' % (nm_kwargs['host'], nm_kwargs['port'],
                               nm_kwargs['device_type'])

    logger.info('Connect to %s', hostinfo)

    try:
        with ConnectHandler(**nm_kwargs) as net_connect:
            if enable:
                logger.debug('Sending enable command to %s', hostinfo)
                net_connect.enable()

            for fname, cmd in filecmddict.items():
                logger.debug('Sending command "%s" to %s', cmd, hostinfo)
                output = net_connect.send_command(cmd)

                if cmd == 'getcurrentconfig':  # uu decode this text
                    output = uu_to_modemconfig(output)

                elif cmd == 'getcurrent':  # sanity-check this text
                    output = check_getcurrent(output, logger)

                logger.debug('Received output from command "%s" from %s',
                             cmd, hostinfo)

                # Q-flex modems can be flaky over-the-air, so we may
                # get empty data or we may want to verify an end string
                # to assure us that we received uncorrupted data
                if ending and not output.endswith(ending):
                    logger.error('Unsaved output from %s to %s. ' +
                                 'Data has bad ending.',
                                 hostinfo, fname)
                elif not output:
                    logger.error(
                            'Unsaved output from %s to %s. Data is empty.',
                            hostinfo, fname)
                else:
                    with open(fname, 'w') as filep:
                        filep.write(output)
                    logger.info('Saved output from %s to %s.', hostinfo, fname)

        logger.info('Disconnect from %s', hostinfo)

    except (IOError, TypeError, ValueError, socket.error, SSHException,
            NetMikoTimeoutException, NetMikoAuthenticationException) as err:
        logger.info('Error with %s: "%s".', hostinfo, err)
    except Exception as err:
        logger.error('Unexpected error with %s: %s', hostinfo, err)


def check_getcurrent(text, logger):
    ''' We expect a bunch of lines that are essentially key=value\n.
        Parse for that and return None when we do not get it. '''

    # CSV reader needs a list or file to read.
    data = csv.reader(text.splitlines(), delimiter='=')
    try:
        dict([(row[0], row[1]) for row in data])
    except IndexError:
        logger.error('Unable to parse output from `getcurrent`. ' +
                     'Set output to None.')
        return None

    return text


def uu_to_modemconfig(uustr):
    '''Take UUEncoded tar.gz data in the form of a string, return the
    ASCII contents of default.conf, which is really quasi-XML data'''

    # Python changed the way it handles strings and binary data to be
    # more explicit in Python 3. As a result, when taking ASCII-based
    # UU data and converting to binary, things get trickier.  The
    # binascii module in Python is well suited to handle this.

    # Take unicode string and convert each UU line to binary, stripping
    # the first and last line in the process.  The 'begin' and 'end'
    # characters on these lines are illegal chars in the binascii
    # module (but not the uu module that we used to use).
    blines = b''
    for line in uustr.splitlines()[1:-1]:
        blines += binascii.a2b_uu(line)

    # Write down uu-decoded binary data, which is a .tgz file
    with NamedTemporaryFile(suffix='.tgz', mode='wb') as tgz:
        tgz.write(blines)
        tgz.seek(0)

        # Read .tgz file
        with tarfile.open(name=tgz.name, mode='r') as tar:
            # Unpack default.conf
            with tar.extractfile('default.conf') as filep:
                modemconfig = filep.read().decode()  # decode to ascii
    return modemconfig


def cfgworker(host, loglevel,
              device_type='linux',
              port=22,
              username='pup',
              password='!!',
              quagga_password='!!',
              quagga_ports=None,
              destination_dir='staging',
              log_dir='/tmp',
              global_delay_factor=10,  # slow for Q-flex
              blocking_timeout=60,     # slow for Q-flex
              ):
    '''Speak to a Teledyne Paradise Q-flex modem using Paradise
    Universal Protocol (PUP). From this, we collect:
    1. Number/Value text data
    2. Key/Value text dara (converted from UUE)
    3. Conditional Quagga data

    For more details, see
    hiseasnet.ucsd.edu/wiki/download/attachments/26148888/QSeriesRemoteControl.pdf
    '''
    logger = setup_logger('collectqflex_%s' % host,
                          os.path.join(log_dir, 'collectqflex.%s.log' % host),
                          level=loglevel)
    bname = re.sub(r'\W', '_', host.split('.')[0])
    destdir = os.path.realpath(destination_dir)

    # Quagga vars
    if quagga_ports is None:
        quagga_ports = {'zebrad': 2601, 'bgpd': 2605}

    qflex_defaults = {
        'blocking_timeout': blocking_timeout,
        'global_delay_factor': global_delay_factor,
        'host': host
    }

    logger.info('BEGIN %s', host)
    myd = qflex_defaults.copy()
    myd.update({'device_type': device_type,
                'password': password,
                'port': port,
                'username': username})
    get_qflex_data({os.path.join(destdir, '.'.join((bname, 'conf'))): 'getcurrentconfig',
                    os.path.join(destdir, 'txt', '.'.join((bname, 'conf'))): 'getcurrent'},
                   myd,
                   logger)

    # Collect Quagga data if DynamicRoutingEnable = On
    try:
        with open(os.path.join(destdir, '%s.%s' % (bname, 'conf')), 'r') as filep:
            conf = filep.read()
    except IOError:
        conf = ''

    if '<set name="DynamicRouterEnable" value="On" />' in conf:
        logger.info('Routing detected for %s; collect Quagga data, too.', host)
        for qname, qport in quagga_ports.items():
            myd = qflex_defaults.copy()
            myd.update({'device_type': 'cisco_ios_telnet',
                        'password': quagga_password,
                        'port': qport,
                        'secret': quagga_password})
            get_qflex_data({os.path.join(destdir, 'quagga',
                                         '.'.join((bname, qname, 'conf'))):
                                             'show running-config'},
                           myd,
                           logger,
                           enable=True,
                           ending='end')

    logger.info('END %s', host)
