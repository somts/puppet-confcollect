# SCP (via Netmiko) config grabber class.
class confcollect::config::getconfs(
  Optional[Stdlib::Absolutepath]          $repodir      = undef,
  Hash                                    $ini_settings = {},
  Optional[Variant[String,Integer,Array]] $hour         = undef,
  Optional[Variant[String,Integer,Array]] $minute       = undef,
) {
  include confcollect

  # CLASS VARIABLES

  $hour_offset  = fqdn_rand(8,$name)

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
    before => Cron['getscp'],
  }

  # MANAGED RESOURCES

  file {
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
  }

  create_ini_settings($ini_settings, {
    path   => "${confcollect::config::_homedir}/etc/getscp.ini",
    before => Cron['getscp'],
  })

  cron { 'getscp':
    user    => $confcollect::owner,
    hour    => $_hour,
    minute  => $_minute,
    command => join([
      "${confcollect::config::_homedir}/bin/getscp.py",
      ">> /var/log/${confcollect::owner}/getscp.log",
      '2>&1',
    ],' '),
  }
}
