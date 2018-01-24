# Configure git for confcollect user
class confcollect::config::git {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # CLASS VARIABLES

  $git_defaults = { user => $confcollect::owner }

  # MANAGED RESOURCES

  git::config {
    'pull.rebase' : * => $git_defaults + { value => 'yes'                 },;
    'push.default': * => $git_defaults + { value => 'simple'              },;
    'user.name'   : * => $git_defaults + { value => $confcollect::comment },;
    'user.email'  : * => $git_defaults + {
      value => "${confcollect::owner}@${confcollect::hostname}",
    },;
  }
}
