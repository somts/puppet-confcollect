## Class: confcollect::params
##
## Parameters for the confcollect module
##
class confcollect::params {

  # VALIDATION
  validate_re($::kernel,'^Linux$',"${::operatingsystem} unsupported")

  # CLASS VARIABLES
  $hostname             = $::fqdn
  $owner                = 'confcollect'
  $group                = $owner
  $comment              = 'Configuration Collector Role'
  $password             = '!!'
  $packages             = ['wget']
  # In order for this to work, $python::dev must be true
  $pip_packages         = ['gitpython','netmiko','paramiko','scp']
  $uid                  = undef
  $gid                  = undef
  $sshkeys              = undef
  $groups               = undef
  $homedir              = undef
  $repobasedir          = undef
  $enable_getpfsense    = false
  $enable_getscp        = false
  $enable_getmediacento = false
}
