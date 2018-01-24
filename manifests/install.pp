# Private class for init.pp
class confcollect::install {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # MANAGED RESOURCES
  include git
  include python
  ensure_packages($confcollect::packages)

  if $confcollect::pip_packages {
    python::pip { $confcollect::pip_packages :
      require => Package[$confcollect::packages],
    }
  }
}
