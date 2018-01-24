## Class: confcollect::params
##
## Parameters for the confcollect module
##
class confcollect::params {

  # VALIDATION
  validate_re($::kernel,'^Linux$',"${::operatingsystem} unsupported")

  # CLASS VARIABLES
  $hostname          = $::fqdn
  $owner             = 'confcollect'
  $group             = $owner
  $comment           = 'Configuration Collector Role'
  $password          = '!!'
  $packages          = ['wget']
  $pip_packages      = ['gitpython']
  $uid               = undef
  $gid               = undef
  $sshkeys           = undef
  $groups            = undef
  $homedir           = undef
  $repobasedir       = undef
  $enable_getpfsense = false
}
