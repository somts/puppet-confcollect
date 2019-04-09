# confcollect

#### Table of Contents

1. [Description](#description)
1. [Setup - The basics of getting started with confcollect](#setup)
    * [What confcollect affects](#what-confcollect-affects)
    * [Setup requirements](#setup-requirements)
    * [Beginning with confcollect](#beginning-with-confcollect)
1. [Usage - Configuration options and additional functionality](#usage)
1. [Reference - An under-the-hood peek at what the module is doing and how](#reference)
1. [Limitations - OS compatibility, etc.](#limitations)
1. [Development - Guide for contributing to the module](#development)

## Description

Confcollect is an in-house module to collect configurations in various
environments and commit them to a git repo(s). It is based on Python
libraries that Ansible uses. Long term, we probably just want to use
Ansible for this purpose, but in the meantime, we set up a custom
Python3 Virtual Environment and do it ourselves.

## Setup

### Beginning with confcollect

Parameters should be obvious, and controlled in Hiera. In particular,
we set up hierarchy for various "projects" that get tuned for
collection.

## Usage

```
include confcollect
```

## Reference

Classes are influenced by puppetlabs-ntp, Puppet Labs' flagship demo
module.

## Limitations

Python module only runs on Linux, so we are Linux-only.

## Development

https://github.com/somts/puppet-confcollect
