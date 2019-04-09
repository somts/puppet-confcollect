# Set up a confcollect role. We use this role account to push and
# pull network device configuration data to a set of repo(s).
class confcollect(
  Hash $repos,
  String $ssh_id,
  String $hostname,
  String $owner,
  String $group,
  String $comment,
  String $password,
  Array $packages,
  Boolean $enable_getconfs,
  Optional[String] $uid,
  Optional[String] $gid,
  Optional[Array] $sshkeys,
  Optional[Array] $groups,
  Hash $getconfs_settings,
  Enum['pip','pip3'] $python_pip_provider,
  Hash $python_pips,
  String $python_version,
  Boolean $python_parameterized,
  Optional[Stdlib::Absolutepath] $homedir,
  Optional[Stdlib::Absolutepath] $python_pyvenv,
  Optional[Stdlib::Absolutepath] $repobasedir,
) {
  # VALIDATION
  validate_re($::kernel,'^Linux$',"${::operatingsystem} unsupported")

  # VARIABLES
  $_homedir = $homedir ? {
    undef   => "/home/${confcollect::owner}",
    default => $homedir,
  }
  $_repobasedir = $repobasedir ? {
    undef   => "${_homedir}/src",
    default => $repobasedir,
  }
  $_python_pyvenv = $python_pyvenv ? {
    undef   => "${_homedir}/pyvenv",
    default => $python_pyvenv,
  }

  # MANAGED RESOURCES
  Class['confcollect::accounts']
  -> Class['confcollect::install']
  -> Class['confcollect::config']

  contain confcollect::accounts
  contain confcollect::install
  contain confcollect::config
}
