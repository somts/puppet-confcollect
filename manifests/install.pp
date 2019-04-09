# Private class for init.pp
class confcollect::install {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # MANAGED RESOURCES
  include git
  ensure_packages($confcollect::packages)

  if $confcollect::python_parameterized {
    class { 'python':
      ensure     => 'present',
      version    => $confcollect::python_version,
      dev        => 'present',
      virtualenv => 'absent', # use Python 3's built-in, pyvenv instead
      require    => [Class['git'],Package[$confcollect::packages]],
    }
  } else {
    # We may want to avoid paramterizing puppet-python, in which case
    # some of the above parameters should be set in the control repo.
    include python
  }

  python::pyvenv { $confcollect::_python_pyvenv :
    owner   => $confcollect::owner,
    group   => $confcollect::group,
    require => [Class['git'],Package[$confcollect::packages]],
  }

  create_resources('python::pip', $confcollect::python_pips, {
    pip_provider => $confcollect::python_pip_provider,
    virtualenv   => $confcollect::_python_pyvenv,
    require      => Python::Pyvenv[$confcollect::_python_pyvenv],
  })
}
