# MediaCento (via Telnet on TCP/24) config grabber class.
class confcollect::config::getmediacento(
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

  # MANAGED RESOURCES

  file { "${confcollect::config::_homedir}/bin/getmediacento.py" :
    ensure => 'file',
    source => 'puppet:///modules/confcollect/getmediacento.py',
    mode   => '0700',
    owner  => $confcollect::owner,
    group  => $confcollect::group,
    before => Cron['getmediacento'],
  }

  create_ini_settings($ini_settings, {
    path   => "${confcollect::config::_homedir}/etc/getmediacento.ini",
    before => Cron['getmediacento'],
  })

  cron { 'getmediacento':
    user    => $confcollect::owner,
    hour    => $_hour,
    minute  => $_minute,
    command => join([
      "${confcollect::config::_homedir}/bin/getmediacento.py",
      ">> /var/log/${confcollect::owner}/getmediacento.log",
      '2>&1',
    ],' '),
  }
}
