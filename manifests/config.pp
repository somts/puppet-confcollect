# Configure confcollect role
class confcollect::config {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # MANAGED RESOURCES
  Class['confcollect::config::files']
  -> Class['confcollect::config::git']
  -> Class['confcollect::config::log']
  -> Class['confcollect::config::repo']
  -> Class['confcollect::config::getconfs']

  contain confcollect::config::files
  contain confcollect::config::git
  contain confcollect::config::log
  contain confcollect::config::repo
  contain confcollect::config::getconfs
}
