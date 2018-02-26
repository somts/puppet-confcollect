# Set up files
class confcollect::config::files {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # CLASS VARIABLES

  $file_defaults = {
    owner => $confcollect::owner,
    group => $confcollect::owner,
    mode  => '2750',
  }

  # MANAGED RESOURCES

  file {
    "${confcollect::config::_homedir}/bin":
      * => $file_defaults + { ensure => 'directory'                 };
    "${confcollect::config::_homedir}/etc":
      * => $file_defaults + { ensure => 'directory'                 };
    "${confcollect::config::_homedir}/lib":
      * => $file_defaults + { ensure => 'directory'                 };
    $confcollect::config::_repobasedir :
      * => $file_defaults + { ensure => 'directory'                 };
    "${confcollect::config::_homedir}/staging":
      * => $file_defaults + { ensure => 'directory'                 };
    "/var/log/${confcollect::owner}":
      * => $file_defaults + { ensure => 'directory', mode => '2755' };
    "${confcollect::config::_homedir}/.ssh/id_rsa":
      * => $file_defaults + {
        ensure  => 'file',
        content => $confcollect::ssh_id,
        mode    => '0600',
     };
    "${confcollect::config::_homedir}/lib/python":
      * => $file_defaults + {
        ensure  => 'directory',
        require => File["${confcollect::config::_homedir}/lib"],
      };
    "${confcollect::config::_homedir}/lib/python/gitcheck.py":
      * => $file_defaults + {
        ensure  => 'file',
        source  => 'puppet:///modules/confcollect/gitcheck.py',
        mode    => '0600',
        require => File["${confcollect::config::_homedir}/lib/python"],
      };
    "${confcollect::config::_homedir}/lib/python/somtsfilelog.py":
      * => $file_defaults + {
        ensure  => 'file',
        source  => 'puppet:///modules/confcollect/somtsfilelog.py',
        mode    => '0600',
        require => File["${confcollect::config::_homedir}/lib/python"],
      };
  }
}
