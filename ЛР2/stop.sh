#!/bin/zsh
LAB=wms2
cd /tmp/$LAB && source env/bin/activate
supervisorctl -c supervisord.conf shutdown || true
eval "$(/opt/homebrew/bin/brew shellenv)" && brew services stop nginx
