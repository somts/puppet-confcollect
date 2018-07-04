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

def write_qflex_file(filename, text, logger):
    '''Take text and save it to file, if it is not empty'''
    logger.debug('Saving output, "%s"' % text)

    if text:
        with open(filename, 'w') as filep:
            filep.write(text)
    else:
        logger.warning('data is empty; not saving to %s.', filename)

    logger.info('conf data saved to %s.', filename)

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
              get_quagga=False,
              global_delay_factor=10, # slow for Q-flex
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
    exceptions = (IOError, ValueError, socket.error, SSHException,
                  NetMikoTimeoutException, NetMikoAuthenticationException)

    filebname = re.sub(r'\W', '_', host.split('.')[0])
    destination_dir = os.path.realpath(destination_dir)

    if quagga_ports is None:
        quagga_ports = [2601, 2605]

    # get the text-based config, then the zipped, uu-encoded config
    cmds = ['getcurrent', 'getcurrentconfig']

    logger.info('BEGIN %s', host)

    try:
        logger.debug('Attempt to talk to %s, SSH TCP/%i.', host, port)
        with ConnectHandler(ip=host,
                            global_delay_factor=global_delay_factor,
                            device_type=device_type,
                            username=username,
                            password=password) as net_connect:

            for cmd in cmds:
                logger.info('Sending command, "%s"...', cmd)
                output = net_connect.send_command(cmd)

                if cmd == 'getcurrent':
                    pup_filename = os.path.join(destination_dir,
                                                'q-flex',
                                                'txt',
                                                '%s.%s' % (filebname, 'conf'))

                elif cmd == 'getcurrentconfig':
                    pup_filename = os.path.join(destination_dir,
                                                'q-flex',
                                                '%s.%s' % (filebname, 'conf'))

                    # Convert UU-encoded data to text
                    output = uu_to_xml(output, logger)
                    if output is None:
                        return

                    # check output for DynamicRoutingEnable = On
                    if '<set name="DynamicRouterEnable" value="On" />' \
                            in output:
                        get_quagga = True

                logger.debug('Received output from command, "%s"...', cmd)

                write_qflex_file(pup_filename, output, logger)
                del pup_filename

        logger.debug('Done talking to %s via SSH.', host)

    except exceptions as err:
        logger.error('SSH error with %s TCP/%i: %s', host, port, err)

    # Conditionally collect Quagga data
    if get_quagga:
        logger.info('Routing detected for %s; collect Quagga data, too.', host)
        for qport in quagga_ports:
            if qport == 2601: # zebrad
                quagga_filename = os.path.join(destination_dir,
                                               'q-flex', 'quagga',
                                               '%s.zebrad.%s' % (filebname, 'conf'))
            elif qport == 2605: # bgpd
                quagga_filename = os.path.join(destination_dir,
                                               'q-flex', 'quagga',
                                               '%s.bgpd.%s' % (filebname, 'conf'))

            get_quagga_running_config(quagga_filename, host, qport,
                                      global_delay_factor,
                                      quagga_password, quagga_password,
                                      logger, exceptions)
            del quagga_filename
    logger.info('END %s', host)

#pylint: enable=too-many-locals

def get_quagga_running_config(filename, host, port, global_delay_factor, secret,
                              password, logger, exceptions):
    '''Login to a Quagga-based service via Telnet, save the running-config'''
    try:
        logger.info('Attempt to talk to %s, Telnet TCP/%i.', host, port)
        with ConnectHandler(ip=host,
                            port=port,
                            device_type='cisco_ios_telnet',
                            global_delay_factor=global_delay_factor,
                            secret=secret,
                            password=password) as net_connect:
            net_connect.enable()
            output = net_connect.send_command('show running-config')
            logger.debug('Received output from command...')
            logger.debug(output)

        logger.info('Done talking to %s, Telnet TCP/%i.', host, port)
        write_qflex_file(filename, output, logger)

    except exceptions as err:
        logger.error('Telnet error with %s TCP/%i: %s', host, port, err)

#pylint: enable=too-many-arguments
