source ENV['GEM_SOURCE'] || 'https://rubygems.org'

### Environment variable version overrrides

# Per puppet enterprise 2016.4, set the versions of critical software.
puppetversion = ENV.key?('PUPPET_VERSION') ? ENV['PUPPET_VERSION'] : '4.10.12'

# Select compatible version of rubocop
rubocopversion = RUBY_VERSION < '2.2.0' ? '< 0.58.0' : '>= 0.58.0'

### Gem requirements
gem 'ci_reporter_rspec'
gem 'facter'
gem 'git'
gem 'hiera-eyaml'
gem 'json_pure'
gem 'kramdown' # for markdown parsing
gem 'metadata-json-lint'
gem 'parallel_tests'
gem 'puppet', puppetversion
gem 'puppet-lint', '>= 1.0.0'

# http://www.camptocamp.com/en/actualite/getting-code-ready-puppet-4/
# gem 'puppet-lint-absolute_classname-check'
gem 'puppet-lint-empty_string-check'
gem 'puppet-lint-leading_zero-check'
gem 'puppet-lint-roles_and_profiles-check'
gem 'puppet-lint-spaceship_operator_without_tag-check'
gem 'puppet-lint-undef_in_function-check'
gem 'puppet-lint-unquoted_string-check'
gem 'puppet-lint-variable_contains_upcase'

gem 'puppet-syntax', require: false
gem 'puppetlabs_spec_helper', '>= 1.0.0'
gem 'rspec-puppet'
gem 'rspec-puppet-facts'

# rspec must be v2 for ruby 1.8.7
if RUBY_VERSION >= '1.8.7' && RUBY_VERSION < '1.9'
  gem 'rake', '~> 10.0'
  gem 'rspec', '~> 2.0'
else
  # rubocop requires ruby >= 1.9, but < 2.2.0 need 0.58.0
  gem 'rubocop', rubocopversion
  gem 'rubocop-rspec'
end
