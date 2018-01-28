# Configure confcollect role
class confcollect::config {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # VARIABLES
  $_homedir = $confcollect::homedir ? {
    undef   => "/home/${confcollect::owner}",
    default => $confcollect::homedir,
  }
  $_repobasedir = $confcollect::repobasedir ? {
    undef   => "${_homedir}/src",
    default => $confcollect::repobasedir,
  }

  # MANAGED RESOURCES
  Class['confcollect::config::accounts'] ->
  Class['confcollect::config::files'] ->
  Class['confcollect::config::git'] ->
  Class['confcollect::config::log'] ->
  Class['confcollect::config::repo']

  contain confcollect::config::accounts
  contain confcollect::config::files
  contain confcollect::config::git
  contain confcollect::config::log
  contain confcollect::config::repo

  if $confcollect::enable_getpfsense {
    Class['confcollect::config::repo']
    -> Class['confcollect::config::getpfsense']
    contain confcollect::config::getpfsense
  }
  if $confcollect::enable_getscp {
    Class['confcollect::config::repo']
    -> Class['confcollect::config::getscp']
    contain confcollect::config::getscp
  }
}
