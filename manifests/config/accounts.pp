# We want to make a user to collect our stuff via push or pull.
class confcollect::config::accounts {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  accounts::user { $confcollect::owner :
    uid           => $confcollect::uid,
    gid           => $confcollect::gid,
    comment       => $confcollect::comment,
    groups        => $confcollect::groups,
    home          => $confcollect::config::_homedir,
    shell         => '/bin/bash',
    membership    => 'inclusive',
    password      => $confcollect::password,
    purge_sshkeys => true,
    system        => true,
    sshkeys       => $confcollect::sshkeys,
  }
}
