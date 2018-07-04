#!/usr/bin/env python
''' collectqflex.py
Talk to various devices, get their config and store.
'''
# Import python built-ins
import os
import re
import tarfile
import uu
from tempfile import NamedTemporaryFile

# Import modules that tend to need a special install
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

from somtsfilelog import setup_logger

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
              username='pup',
              password='!!',
              quagga_password='!!',
              quagga_ports=None,
              destination_dir='staging',
              log_dir='/tmp',
              get_quagga=False,
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

    if quagga_ports is None:
        quagga_ports = [2601, 2605]

    # get the text-based config, then the zipped, uu-encoded config
    commands = ['getcurrent', 'getcurrentconfig']

    logger.info('BEGIN %s', host)

    try:
        logger.debug('Attempt to connect to host %s, device type %s',
                     host, device_type)
        with ConnectHandler(ip=host,
                            global_delay_factor=3, # slow for Q-flex
                            device_type=device_type,
                            username=username,
                            password=password) as net_connect:

            for command in commands:
                logger.debug('Sending command, "%s"...', command)
                output = net_connect.send_command(command)

                if command == 'getcurrent':
                    dest_filename = os.path.join(os.path.realpath(destination_dir),
                                                 'q-flex_puptxt',
                                                 '%s.%s' % (filebname, 'txt'))

                elif command == 'getcurrentconfig':
                    dest_filename = os.path.join(os.path.realpath(destination_dir),
                                                 'q-flex_pup',
                                                 '%s_xml.%s' % (filebname, 'conf'))
                    # Convert UU-encoded data to text
                    output = uu_to_xml(output, logger)
                    if output is None:
                        return

                    # check output for DynamicRoutingEnable = On
                    if '<set name="DynamicRouterEnable" value="On" />' \
                            in output:
                        get_quagga = True

                logger.debug('Received output from command, "%s"...', command)
                logger.debug(output)

                with open(dest_filename, 'w') as filep:
                    filep.write(output)
                logger.debug('conf data saved to %s.', dest_filename)

        logger.debug('Done talking to %s via SSH.', host)

    except NetMikoTimeoutException as err:
        logger.error('Error with %s: %s', host, err)

    # Conditionally collect Quagga data
    if get_quagga:
        logger.info('Routing detected for %s; collect Quagga data, too.', host)
        for port in quagga_ports:
            try:
                logger.debug('Attempt to talk to %s, Telnet TCP/%i.', host, port)
                with ConnectHandler(ip=host,
                                    port=port,
                                    device_type='cisco_ios_telnet',
                                    global_delay_factor=3, # slow for Q-flex
                                    secret=quagga_password,
                                    password=quagga_password) as net_connect:
                    net_connect.enable()
                    output = net_connect.send_command('show running-config')
                    logger.debug('Received output from command...')
                    logger.debug(output)

                logger.debug('Done talking to %s, Telnet TCP/%i.', host, port)

                if port == 2601: # zebrad
                    dest_filename = os.path.join(os.path.realpath(destination_dir),
                                                 'q-flex_zebrad',
                                                 '%s.%s' % (filebname, 'conf'))
                elif port == 2605: # bgpd
                    dest_filename = os.path.join(os.path.realpath(destination_dir),
                                                 'q-flex_bgpd',
                                                 '%s_bgpd.%s' % (filebname, 'conf'))

                with open(dest_filename, 'w') as filep:
                    filep.write(output)
                logger.debug('conf data saved to %s.', dest_filename)

            except NetMikoTimeoutException as err:
                logger.error('Error with %s: %s', host, err)

    logger.info('END %s', host)
#pylint: enable=too-many-arguments
#pylint: enable=too-many-locals
