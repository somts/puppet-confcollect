# Set up confcollect repos
class confcollect::config::repo {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # CLASS VARIABLES

  $repo_defaults = {
    ensure   => 'latest',
    provider => 'git',
    revision => 'master',
    user     => $confcollect::owner,
    owner    => $confcollect::owner,
    group    => $confcollect::group,
  }

  # MANAGED RESOURCES

  $confcollect::repos.each |String $dir, Hash $settings| {
    vcsrepo { "${confcollect::config::_repobasedir}/${dir}":
      * => $repo_defaults + $settings
    }
  }
}
