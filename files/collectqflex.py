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

#pylint: disable=too-many-arguments
def get_qflex_data(filenames, cmds, logger, nm_kwargs, enable=False, ending=None):
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
                    # Q-flex modems can be flaky over-the-air, so
                    # we may want to verify an end string to assure us
                    # that we received uncorrupted data.
                    if ending and not output.endswith(ending):
                        logger.error('Unsaved to %s. Data does end with "%s"',
                                     filename, ending)
                        writefile = False
                    else:
                        writefile = True

                    logger.debug(output)

                    if writefile:
                        logger.debug('Saving output, "%s"' % output)
                        with open(filename, 'w') as filep:
                            filep.write(output)
                        logger.info('Saved to %s.', filename)
                else:
                    logger.warning('Unsaved to %s. Data is empty.', filename)

        logger.info('Disconnect from %s', hostinfo)

    except (IOError, ValueError, socket.error, SSHException,
            NetMikoTimeoutException, NetMikoAuthenticationException) as err:
        logger.info('Error with %s: "%s".', hostinfo, err)
#pylint: enable=too-many-arguments

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
        quagga_ports = {'zebrad': 2601, 'bgpd': 2605}

    # PUP vars
    pcmds = ['getcurrentconfig', 'getcurrent']
    pfilenames = [os.path.join(destination_dir, 'q-flex',
                               '%s.%s' % (filebname, 'conf')),
                  os.path.join(destination_dir, 'q-flex', 'txt',
                               '%s.%s' % (filebname, 'conf'))]

    logger.info('BEGIN %s', host)
    get_qflex_data(pfilenames, pcmds, logger,
                   {
                       'blocking_timeout': blocking_timeout,
                       'device_type': device_type,
                       'global_delay_factor': global_delay_factor,
                       'host': host,
                       'password': password,
                       'port': port,
                       'username': username,
                   })

    # Collect Quagga data if DynamicRoutingEnable = On
    try:
        with open(pfilenames[0], 'r') as filep:
            default_conf = filep.read()
    except IOError:
        default_conf = ''

    if '<set name="DynamicRouterEnable" value="On" />' in default_conf:
        logger.info('Routing detected for %s; collect Quagga data, too.', host)
        for qname, qport in quagga_ports:
            get_qflex_data([os.path.join(destination_dir, 'q-flex', 'quagga',
                                         '%s.%s.%s' % (filebname, qname, 'conf'))],
                           qcmds,
                           logger,
                           {
                               'blocking_timeout': blocking_timeout,
                               'device_type': 'cisco_ios_telnet',
                               'global_delay_factor': global_delay_factor,
                               'host': host,
                               'password': quagga_password,
                               'port': qport,
                               'secret': quagga_password,
                           },
                           enable=True,
                           ending='end')

    logger.info('END %s', host)
#pylint: enable=too-many-locals
#pylint: enable=too-many-arguments
