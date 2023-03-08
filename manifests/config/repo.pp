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
    require  => Git::Config['safe.directory'],
  }

  # MANAGED RESOURCES
  
  # WORKAROUND: we need a way to specify multiple safe dirs but Git and
  # Puppet do not want to play nice together at this time
  git::config { 'safe.directory':
    value => '*', 
    scope => system,
  }

  $confcollect::repos.each |String $dir, Hash $settings| {
    vcsrepo { "${confcollect::_repobasedir}/${dir}":
      * => $repo_defaults + $settings
    }
  }
}
