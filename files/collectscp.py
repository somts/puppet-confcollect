# THIS FILE MANANGED BY PUPPET.
''' collectscp.py

    Config grabber via Netmiko/SCP. Used to keep various
    SSH/SCP-capable config file(s) up-to-date from various locations.'''

from pathlib import Path
from netmiko import ConnectHandler, SCPConn
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import NetMikoAuthenticationException
from paramiko.ssh_exception import SSHException
from scp import SCPException

from somtsfilelog import setup_logger


def cfgworker(host, loglevel,
              device_type='cisco_ios',
              username='admin',
              password='!!',
              destination_dir='/tmp',
              remote_filename='nvram:startup-config',
              log_dir='/tmp',
              filename_extension='cfg',
              local_filename=None,
              hostname=None,
              preserve_times=False,
              recursive=False,
              sort=False
              ):
    '''Multiprocessing worker for get_cfg()'''

    # host and hostname are the same thing unless overridden
    hostname = host if hostname is None else hostname

    logger = setup_logger(
            f'collectscp_{hostname}',
            Path(log_dir).joinpath(f'collectscp.{hostname}.log'),
            level=loglevel)

    logger.info('BEGIN %s', host)

    destp = Path(destination_dir).absolute()

    if local_filename is None:
        local_filename = destp.joinpath('%s.%s' % (hostname.split('.')[0],
                                                   filename_extension))
    else:
        # ignore destination_dir when local_filename is provided
        # ... unless local_filename is relative
        if not Path(local_filename).is_absolute():
            local_filename = destp.joinpath(local_filename)

        destp = Path(local_filename).parent()

    try:  # Attempt to ensure dir exists
        destp.mkdir(parents=True, exist_ok=True)
    except (FileNotFoundError, PermissionError) as err:
        logger.error('Error with target dir %s: %s', destp, err)
    except Exception as err:
        logger.error('Unexpected error with target dir %s: %s', destp, err)

    try:
        logger.debug('Attempt to SSH to host %s, device type %s',
                     host, device_type)
        with ConnectHandler(host=host,
                            device_type=device_type,
                            username=username,
                            password=password) as net_connect:
            net_connect.enable()
            logger.debug('Attempt to connect via SCP...')
            try:
                scp_conn = SCPConn(net_connect)
                scp_conn.scp_client.get(remote_filename, local_filename,
                                        recursive=recursive,
                                        preserve_times=preserve_times)
                logger.info('Config for %s:%s transferred successfully to %s.',
                            host, remote_filename, local_filename)
                scp_conn.close()

                # files like esx.conf come to us in varying order,
                # which makes some of the changes we track not very
                # helpful. So, we offer a way to sort the file lines
                # to work around issues like that.
                if sort and not recursive:
                    logger.info('Sorting contents of %s', local_filename)
                    with open(local_filename, 'r+') as filep:
                        sortf = sorted(filep)    # sort file
                        filep.seek(0)            # goto start of file
                        filep.writelines(sortf)  # overwrite
                        filep.truncate()         # cut off any remainder
            except (EOFError, SCPException, SSHException) as err:
                logger.error('Error with %s: %s', host, err)
            except Exception as err:
                logger.error('Unexpected error with %s: %s', host, err)

    except (EOFError,
            SSHException,
            NetMikoTimeoutException,
            NetMikoAuthenticationException) as err:
        logger.error('Error with %s: %s', host, err)
    except Exception as err:
        logger.error('Unexpected error with %s: %s', host, err)

    logger.info('END %s', host)
