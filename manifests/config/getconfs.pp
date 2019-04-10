# SCP (via Netmiko) config grabber class.
class confcollect::config::getconfs(
  Optional[Stdlib::Absolutepath]          $repodir  = undef,
  Hash                                    $settings = {},
  Optional[Variant[String,Integer,Array]] $hour     = undef,
  Optional[Variant[String,Integer,Array]] $minute   = undef,
) {
  include confcollect

  # CLASS VARIABLES
  $venv = $confcollect::_python_pyvenv

  $cron_ensure = $confcollect::enable_getconfs ? {
    true    => 'present',
    default => 'absent',
  }

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
  create_resources('file',{
    "${confcollect::_homedir}/etc/getconfs.json"  => {
      content => to_json_pretty($confcollect::getconfs_settings),
    },
    "${confcollect::_homedir}/bin/getconfs"       => {
      content => template('confcollect/getconfs.epp'),
      mode    => '0700',
    },
    "${confcollect::_python_pyvenv}/getconfs.py"          => {
      source => 'puppet:///modules/confcollect/getconfs.py',
    },
    "${confcollect::_python_pyvenv}/collectadvantech.py"  => {
      source => 'puppet:///modules/confcollect/collectadvantech.py',
    },
    "${confcollect::_python_pyvenv}/collectmediacento.py" => {
      source => 'puppet:///modules/confcollect/collectmediacento.py',
    },
    "${confcollect::_python_pyvenv}/collectpfsense.py"    => {
      source => 'puppet:///modules/confcollect/collectpfsense.py',
    },
    "${confcollect::_python_pyvenv}/collectqflex.py"      => {
      source => 'puppet:///modules/confcollect/collectqflex.py',
    },
    "${confcollect::_python_pyvenv}/collectscp.py"        => {
      source => 'puppet:///modules/confcollect/collectscp.py',
    },
    "${confcollect::_python_pyvenv}/collectssh.py"        => {
      source => 'puppet:///modules/confcollect/collectssh.py',
    },
    "${confcollect::_python_pyvenv}/gitcheck.py"          => {
        source  => 'puppet:///modules/confcollect/gitcheck.py',
    },
    "${confcollect::_python_pyvenv}/somtsfilelog.py"      => {
        source  => 'puppet:///modules/confcollect/somtsfilelog.py',
    },
  },{
    ensure => 'file',
    owner  => $confcollect::owner,
    group  => $confcollect::owner,
    mode   => '0600',
    before => Cron['getconfs'],
  })

  # purge legacy
  create_resources('file',{
    "${confcollect::_homedir}/bin/getconfs.py" => {},
    "${confcollect::_homedir}/lib"             => {
      purge   => true,
      recurse => true,
      force   => true,
    },
  },{ ensure => 'absent' })

  cron { 'getconfs':
    ensure  => $cron_ensure,
    user    => $confcollect::owner,
    hour    => $_hour,
    minute  => $_minute,
    command => "${confcollect::_homedir}/bin/getconfs",
  }
}
