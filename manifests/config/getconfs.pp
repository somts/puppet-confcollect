# SCP (via Netmiko) config grabber class.
class confcollect::config::getconfs(
  Optional[Stdlib::Absolutepath]          $repodir      = undef,
  Hash                                    $ini_settings = {},
  Optional[Variant[String,Integer,Array]] $hour         = undef,
  Optional[Variant[String,Integer,Array]] $minute       = undef,
) {
  include confcollect

  # CLASS VARIABLES
  $cron_ensure = $confcollect::enable_getconfs ? {
    true    => 'present',
    default => 'absent',
  }

  $hour_offset  = fqdn_rand(8,$name)

  $_ini_settings = empty($confcollect::getconfs_ini_settings) ? {
    true    => $ini_settings,
    default => $confcollect::getconfs_ini_settings,
  }

  # By default, we try and collect 3 times a day. We need the hour and
  # minute set randomly in order to splay out git commits and avoid
  # conflicts with multiple nodes trying to commit to the same branch
  # at once.
  $_hour = $hour ? {
    undef   => [$hour_offset, $hour_offset + 8, $hour_offset + 16],
    default => $hour,
  }
  $_minute = $minute ? {
    undef   => fqdn_rand(59,$name),
    default => $minute,
  }
  $file_defaults = {
    ensure => 'file',
    owner  => $confcollect::owner,
    group  => $confcollect::owner,
    mode   => '0600',
    before => Cron['getconfs'],
  }

  # MANAGED RESOURCES

  file {
    "${confcollect::config::_homedir}/etc/getconfs.ini":
      * => $file_defaults + {
        content => template('confcollect/getconfs.erb'),
      };
    "${confcollect::config::_homedir}/bin/getconfs.py" :
      * => $file_defaults + {
        source => 'puppet:///modules/confcollect/getconfs.py',
        mode   => '0700',
      };
    "${confcollect::config::_homedir}/lib/python/collectmediacento.py":
      * => $file_defaults + {
        source  => 'puppet:///modules/confcollect/collectmediacento.py',
      };
    "${confcollect::config::_homedir}/lib/python/collectpfsense.py":
      * => $file_defaults + {
        source  => 'puppet:///modules/confcollect/collectpfsense.py',
      };
    "${confcollect::config::_homedir}/lib/python/collectscp.py":
      * => $file_defaults + {
        source  => 'puppet:///modules/confcollect/collectscp.py',
      };
    "${confcollect::config::_homedir}/lib/python/collectssh.py":
      * => $file_defaults + {
        source  => 'puppet:///modules/confcollect/collectssh.py',
      };
  }

  cron { 'getconfs':
    ensure  => $cron_ensure,
    user    => $confcollect::owner,
    hour    => $_hour,
    minute  => $_minute,
    command => "${confcollect::config::_homedir}/bin/getconfs.py -g",
  }
}
