#!/bin/bash
# THIS FILE MANANGED BY PUPPET.

[ -d $1 ] && cd $1 && \
if [ `git status --porcelain | wc -l` -gt 0 ]; then
  git add -A && \
  git commit -a -m "confcollect update, $HOSTNAME (`date`)" && \
  git pull --rebase && \
  git push
fi
