#!/usr/bin/env python
''' collectqflex.py
Talk to various devices, get their config and store.
'''
# Import python built-ins
import os
import re
import tarfile
import socket
import uu
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

                if cmd == 'getcurrentconfig': # uu decode this text
                    output = uu_to_xml(output, logger)

                logger.debug('Received output from command "%s" from %s',
                             cmd, hostinfo)

                # Q-flex modems can be flaky over-the-air, so we may
                # get empty data or we may want to verify an end string
                # to assure us that we received uncorrupted data
                if not output or (ending and not output.endswith(ending)):
                    logger.error('Unsaved output from %s to %s. ' +
                                 'Data is empty or has a bad ending.',
                                 hostinfo, fname)
                else:
                    with open(fname, 'w') as filep:
                        filep.write(output)
                    logger.info('Saved output from %s to %s.', hostinfo, fname)

        logger.info('Disconnect from %s', hostinfo)

    except (IOError, ValueError, socket.error, SSHException,
            NetMikoTimeoutException, NetMikoAuthenticationException) as err:
        logger.info('Error with %s: "%s".', hostinfo, err)

def uu_to_xml(uue, logger):
    '''Take UUEncoded tar.gz data, return the contents of
    default.conf, which is really quasi-XML data'''

    # Write down our UUE data, decode
    with NamedTemporaryFile(suffix='.txt') as uuin:
        uuin.write(uue)
        uuin.seek(0)
        # Need a temporary filename for our .tar.gz file
        uuout = NamedTemporaryFile(suffix='.tgz', delete=False)
        os.unlink(uuout.name)
        try:
            uu.decode(uuin.name, uuout.name)
        except uu.Error as err:
            logger.error('Error with UUE data: %s', err)
            return None

    # The data is a tarball. Get default.conf out of it.
    with tarfile.open(name=uuout.name, mode='r') as tar:
        filep = tar.extractfile('default.conf')
        xml = filep.read()
        filep.close()
    os.unlink(uuout.name)

    return xml

#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals
def cfgworker(host, loglevel,
              device_type='linux',
              port=22,
              username='pup',
              password='!!',
              quagga_password='!!',
              quagga_ports=None,
              destination_dir='staging',
              log_dir='/tmp',
              global_delay_factor=10, # slow for Q-flex
              blocking_timeout=60,    # slow for Q-flex
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
    get_qflex_data({os.path.join(destdir, '.'.join((bname, 'conf'))): 'getcurrentconfig',
                    os.path.join(destdir, 'txt', '.'.join((bname, 'conf'))): 'getcurrent'},
                   dict(qflex_defaults.items() + {
                       'device_type': device_type,
                       'password': password,
                       'port': port,
                       'username': username,
                   }.items()),
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
            get_qflex_data({os.path.join(destdir, 'quagga',
                                         '.'.join((bname, qname, 'conf'))): \
                                             'show running-config',
                           },
                           dict(qflex_defaults.items() + {
                               'device_type': 'cisco_ios_telnet',
                               'password': quagga_password,
                               'port': qport,
                               'secret': quagga_password,
                           }.items()),
                           logger,
                           enable=True,
                           ending='end')

    logger.info('END %s', host)
#pylint: enable=too-many-locals
#pylint: enable=too-many-arguments
