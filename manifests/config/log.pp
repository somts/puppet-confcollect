# Set up confcollect logging
class confcollect::config::log {

  # VALIDATION
  assert_private('This class should only be called from the init class')

  # MANAGED RESOURCES

  logrotate::rule { $confcollect::owner :
    compress      => true,
    delaycompress => true,
    missingok     => true,
    path          => "/var/log/${confcollect::owner}/*.log",
    rotate        => 7,
    rotate_every  => 'day',
    require       => File["/var/log/${confcollect::owner}"],
  }
}
