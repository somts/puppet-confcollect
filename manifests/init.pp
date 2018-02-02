# Set up a confcollect role. We use this role account to push and
# pull network device configuration data to a set of repo(s).
class confcollect(
  Hash $repos,
  String $ssh_id,
  String $hostname                        = $confcollect::params::hostname,
  String $owner                           = $confcollect::params::owner,
  String $comment                         = $confcollect::params::comment,
  String $password                        = $confcollect::params::password,
  Array $packages                         = $confcollect::params::packages,
  Boolean $enable_getscp                  = $confcollect::params::enable_getscp,
  Boolean $enable_getpfsense
  = $confcollect::params::enable_getpfsense,
  Boolean $enable_getmediacento
  = $confcollect::params::enable_getmediacento,
  Optional[Array] $pip_packages           = $confcollect::params::pip_packages,
  Optional[String] $uid                   = $confcollect::params::uid,
  Optional[String] $gid                   = $confcollect::params::gid,
  Optional[Array] $sshkeys                = $confcollect::params::sshkeys,
  Optional[Array] $groups                 = $confcollect::params::groups,
  Optional[Stdlib::Absolutepath] $homedir = $confcollect::params::homedir,
  Optional[Stdlib::Absolutepath] $repobasedir
  = $confcollect::params::repobasedir,
) inherits confcollect::params {

  Class['confcollect::install']-> Class['confcollect::config']

  contain confcollect::install
  contain confcollect::config
}
