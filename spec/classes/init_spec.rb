require 'spec_helper'
describe 'confcollect' do

  shared_context 'Supported Platform' do
    let :params do {
      :ssh_id => 'foo',
      :repos  => {
        'git_repo'   => { 'source' => 'https://example.com/git_repo.git'   },
        'other_repo' => { 'source' => 'https://example.com/other_repo.git' },
      },
    } end

    it { should compile.with_all_deps }
    it { should contain_class('confcollect') }

    # Install
    it { should contain_class('confcollect::install').that_comes_before(
      'Class[confcollect::config]') }
    it { should contain_class('git') }
    it { should contain_class('python') }
    it { should contain_package('wget') }
    it { should contain_python__pip('gitpython') }

    # Config
    it { should contain_class('confcollect::config') }
    it { should contain_class('confcollect::config::accounts').that_comes_before(
      'Class[confcollect::config::files]') }
    it { should contain_class('confcollect::config::files').that_comes_before(
      'Class[confcollect::config::git]') }
    it { should contain_class('confcollect::config::git').that_comes_before(
      'Class[confcollect::config::log]') }
    it { should contain_class('confcollect::config::repo') }

    # Config::Accounts
    it { should contain_accounts__user('confcollect').with({
      :comment       => 'Configuration Collector Role',
      :password      => '!!',
      :purge_sshkeys => true,
      :system        => true,
      :shell         => '/bin/bash',
      :membership    => 'inclusive',
    }) }

    # Config::Files
    it { should contain_file('/home/confcollect/bin').with_ensure('directory') }
    it { should contain_file('/home/confcollect/etc').with_ensure('directory') }
    it { should contain_file('/home/confcollect/src').with_ensure('directory') }
    it { should contain_file('/home/confcollect/staging').with_ensure('directory') }
    it { should contain_file('/var/log/confcollect').with_ensure('directory') }
    it { should contain_file('/home/confcollect/.ssh/id_rsa').with({
      :ensure  => 'file',
      :mode    => '0600',
      :content => 'foo',
    }) }

    # Config::Repo
    it { should contain_vcsrepo('/home/confcollect/src/git_repo').with({
      :ensure   => 'latest',
      :source   => 'https://example.com/git_repo.git',
      :provider => 'git',
    }) }
    it { should contain_vcsrepo('/home/confcollect/src/other_repo') }

    context 'with getconfs enabled' do
      let :params do {
        :ssh_id          => 'foo',
        :enable_getconfs => true,
        :repos           => { 'pfsense' => {
          'source' => 'https://example.com/pfsense.git'}
        },
      } end
      it { should contain_class('confcollect::config::getconfs').that_requires(
        'Class[confcollect::config::repo]') }
      it { should contain_file('/home/confcollect/bin/getconfs.py').with({
        :ensure => 'file',
        :mode   => '0700',
        :owner  => 'confcollect',
        :group  => 'confcollect',
      }).that_comes_before('Cron[getconfs]') }
      it { should contain_cron('getconfs').with_user('confcollect') }
    end
  end

  shared_examples 'Darwin' do
    it { should_not compile.with_all_deps }
  end

  shared_examples 'Debian' do
    it { should_not compile.with_all_deps }
    it_behaves_like 'Supported Platform'
  end

  shared_examples 'RedHat' do
    it { should_not compile.with_all_deps }
    it_behaves_like 'Supported Platform'
  end

  [ { :osfamily                  => 'RedHat' ,
      :kernel                    => 'Linux',
      :architecture              => 'x86_64',
      :puppetversion             => '4.10.5',
      :operatingsystemmajrelease => '7',
      :operatingsystemrelease    => '7.4.1708',
      :operatingsystem           => 'CentOS',
    },
    { :osfamily                  => 'Debian' ,
      :kernel                    => 'Linux',
      :architecture              => 'amd64' ,
      :lsbdistcodename           => 'xenial',
      :puppetversion             => '4.10.5',
      :operatingsystemrelease    => '16.04',
      :operatingsystemmajrelease => '16.04',
      :operatingsystem           => 'Ubuntu',
    },
    { :osfamily                  => 'Darwin' ,
      :kernel                    => 'Darwin',
      :architecture              => 'x86_64',
      :puppetversion             => '4.10.5',
      :operatingsystemrelease    => '17.3.0',
      :operatingsystem           => 'Darwin',
    },
  ].each do |myfacts|
    context myfacts[:osfamily] do
      let :facts do myfacts end

      case myfacts[:osfamily]
      when 'Darwin'  then it_behaves_like 'Darwin'
      when 'Debian'  then it_behaves_like 'Debian'
      when 'RedHat'  then it_behaves_like 'RedHat'
      end
    end
  end
end
