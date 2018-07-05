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

def get_qflex_data(filenames, cmds, logger, nm_kwargs, enable=False):
    '''Login to a Netmiko service, save output of a command'''

    hostinfo = '%s:%i (%s)' % (nm_kwargs['host'], nm_kwargs['port'],
                               nm_kwargs['device_type'])

    logger.info('Connect to %s', hostinfo)
    try:
        with ConnectHandler(**nm_kwargs) as net_connect:
            if enable:
                net_connect.enable()

            for cmd, filename in zip(cmds, filenames):
                output = net_connect.send_command(cmd)

                if cmd == 'getcurrentconfig': # uu decode this text
                    output = uu_to_xml(output, logger)

                logger.debug('Received output from command, "%s":', cmd)

                if output:

                    logger.debug(output)
                    logger.debug('Saving output, "%s"' % output)

                    with open(filename, 'w') as filep:
                        filep.write(output)

                    logger.info('data saved to %s.', filename)
                else:
                    logger.warning('data is empty; not saving to %s.', filename)

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
    filebname = re.sub(r'\W', '_', host.split('.')[0])
    destination_dir = os.path.realpath(destination_dir)

    # Quagga vars
    qcmds = ['show running-config']
    if quagga_ports is None:
        quagga_ports = [2601, 2605]

    # PUP vars
    pcmds = ['getcurrentconfig', 'getcurrent']
    pfilenames = [os.path.join(destination_dir, 'q-flex',
                               '%s.%s' % (filebname, 'conf')),
                  os.path.join(destination_dir, 'q-flex', 'txt',
                               '%s.%s' % (filebname, 'conf'))]
    netmiko_ssh_kwargs = {
        'host': host,
        'port': port,
        'global_delay_factor': global_delay_factor,
        'blocking_timeout': blocking_timeout,
        'device_type': device_type,
        'username': username,
        'password': password,
    }

    logger.info('BEGIN %s', host)
    get_qflex_data(pfilenames, pcmds, logger, netmiko_ssh_kwargs)

    # Collect Quagga data if DynamicRoutingEnable = On
    with open(pfilenames[0], 'r') as filep:
        default_conf = filep.read()

    if '<set name="DynamicRouterEnable" value="On" />' in default_conf:
        logger.info('Routing detected for %s; collect Quagga data, too.', host)
        for qport in quagga_ports:

            netmiko_telnet_kwargs = {
                'device_type': 'cisco_ios_telnet',
                'host': host,
                'port': qport,
                'global_delay_factor': global_delay_factor,
                'blocking_timeout': blocking_timeout,
                'secret': quagga_password,
                'password': quagga_password,
            }

            if qport == 2601: # zebrad
                qfilenames = [os.path.join(destination_dir,
                                           'q-flex', 'quagga',
                                           '%s.zebrad.%s' % (filebname, 'conf'))]
            elif qport == 2605: # bgpd
                qfilenames = [os.path.join(destination_dir,
                                           'q-flex', 'quagga',
                                           '%s.bgpd.%s' % (filebname, 'conf'))]

            get_qflex_data(qfilenames, qcmds, logger,
                           netmiko_telnet_kwargs, enable=True)

            del qfilenames, netmiko_telnet_kwargs

    logger.info('END %s', host)
#pylint: enable=too-many-locals
#pylint: enable=too-many-arguments
