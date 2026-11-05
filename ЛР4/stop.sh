#!/bin/zsh
LAB=wms4
cd /tmp/$LAB && source env/bin/activate
supervisorctl -c supervisord.conf shutdown || true
eval "$(/opt/homebrew/bin/brew shellenv)" && brew services stop nginx
