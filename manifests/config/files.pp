# Set up files
class confcollect::config::files {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # CLASS VARIABLES

  $file_defaults = {
    ensure  => 'directory',
    owner   => $confcollect::owner,
    group   => $confcollect::owner,
    mode    => '2750',
  }

  # MANAGED RESOURCES

  file {
    $confcollect::_repobasedir: * => $file_defaults;
    "${confcollect::_homedir}/staging": * => $file_defaults;
    "/var/log/${confcollect::owner}": * => $file_defaults + { mode => '2755' };
    "${confcollect::_homedir}/bin":
      * => $file_defaults + { purge => true, recurse => true };
    "${confcollect::_homedir}/etc":
      * => $file_defaults + { purge => true, recurse => true };
    "${confcollect::_homedir}/.ssh/id_rsa":
      * => $file_defaults + {
        ensure  => 'file',
        content => $confcollect::ssh_id,
        mode    => '0600',
      };
  }
}
