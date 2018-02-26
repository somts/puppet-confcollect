# THIS FILE MANANGED BY PUPPET.
''' collectscp.py

    Config grabber via Netmiko/SCP. Used to keep various
    SSH/SCP-capable config file(s) up-to-date from various locations.'''

from os import path
from netmiko import ConnectHandler, SCPConn
from netmiko.ssh_exception import NetMikoTimeoutException

from somtsfilelog import setup_logger

#pylint: disable-msg=too-many-arguments
def cfgworker(host, loglevel,
              device_type='cisco_ios',
              username='admin',
              password='!!',
              destination_dir='/tmp',
              remote_filename='nvram:startup-config',
              log_dir='/tmp',
              filename_extension='cfg',
              local_filename=None
             ):
    '''Multiprocessing worker for get_cfg()'''

    logger = setup_logger('collectscp_%s' % host,
                          path.join(log_dir, 'collectscp.%s.log' % host),
                          level=loglevel)
    logger.info('BEGIN %s', host)

    if local_filename is None:
        local_filename = path.join(path.realpath(destination_dir),
                                   '%s.%s' % (host.split('.')[0],
                                              filename_extension))

    try:
        logger.debug('Attempt to connect to host %s, device type %s', host, device_type)
        net_connect = ConnectHandler(ip=host,
                                     device_type=device_type,
                                     username=username,
                                     password=password)

        net_connect.enable()
        logger.debug('Attempt to connect to SCP daemon...')
        scp_conn = SCPConn(net_connect)
        scp_conn.scp_get_file(remote_filename, local_filename)
        logger.info('Configuration for %s:%s transferred successfully to %s.',
                    host, remote_filename, local_filename)
        scp_conn.close()

    except NetMikoTimeoutException as err:
        logger.error('Error with %s: %s', host, err)

    logger.info('END %s', host)
#pylint: enable-msg=too-many-arguments
