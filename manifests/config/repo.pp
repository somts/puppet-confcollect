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
    git::config { "${confcollect::_repobasedir}/${dir}":
      key   => 'safe.directory',
      value => "${confcollect::_repobasedir}/${dir}",
      scope => system,
    }->
    vcsrepo { "${confcollect::_repobasedir}/${dir}":
      * => $repo_defaults + $settings
    }
  }
}
