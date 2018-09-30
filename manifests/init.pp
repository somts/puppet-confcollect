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
  Optional[Array] $pip_packages,
  Optional[String] $uid,
  Optional[String] $gid,
  Optional[Array] $sshkeys,
  Optional[Array] $groups,
  Hash $getconfs_settings,
  Optional[Stdlib::Absolutepath] $homedir,
  Optional[Stdlib::Absolutepath] $repobasedir,
) {
  # VALIDATION
  validate_re($::kernel,'^Linux$',"${::operatingsystem} unsupported")

  Class['confcollect::install']-> Class['confcollect::config']

  contain confcollect::install
  contain confcollect::config
}
