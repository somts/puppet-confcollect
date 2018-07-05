# THIS FILE MANANGED BY PUPPET.
''' collectssh.py

    Config grabber via Netmiko/SSH typically to a Cisco SG-300. Used to
    keep SG-300 switches and the like up-to-date from various locations
    by making the device send its config to our collector.'''
from os import path, rename
from socket import gethostbyname, gethostname
from getpass import getuser
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException

from somtsfilelog import setup_logger

#pylint: disable-msg=too-many-arguments
#pylint: disable-msg=too-many-locals
def cfgworker(host, loglevel,
              device_type='cisco_s300',
              username='admin',
              password='!!',
              destination_dir='staging',
              remote_filename='flash://startup-config',
              log_dir='/tmp',
              filename_extension='cfg',
              dest_filename=None,
              dest_username=None,
              dest_password=None,
              dest_host=None
             ):
    '''Multiprocessing worker for collectssh'''

    logger = setup_logger('collectssh_%s' % host,
                          path.join(log_dir, 'collectssh.%s.log' % host),
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

    # Delicate hack: scp on ye olde SG-300s appears to be extra dumb
    # and we can only plop files in a user's homedir. We do that, and
    # then move the file where we want it.
    dest_basename = path.basename(dest_filename)

    command = ' '.join(['copy', remote_filename, 'scp://%s:%s@%s/%s' %
                        (dest_username, dest_password,
                         dest_host, dest_basename)])

    try:
        logger.debug('Attempt to connect to host %s, device type %s',
                     host, device_type)
        with ConnectHandler(host=host,
                            device_type=device_type,
                            username=username,
                            password=password) as net_connect:
            net_connect.enable()
            logger.debug('Sending command, "%s"...', command)
            output = net_connect.send_command(command)
            logger.info(output)

        # Once copied, move file into place
        tempfile = path.join(path.expanduser('~'), dest_basename)
        logger.info('Moving %s to %s.', tempfile, dest_filename)
        rename(tempfile, dest_filename)

    except NetMikoTimeoutException as err:
        logger.error('Error with %s: %s', host, err)

    logger.info('END %s', host)
#pylint: enable-msg=too-many-arguments
#pylint: enable-msg=too-many-locals
