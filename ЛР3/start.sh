#!/bin/zsh
set -e
setopt NULL_GLOB
LAB=wms3
DIR="$(cd "$(dirname "$0")" && pwd)"
ln -sfn "$DIR" /tmp/$LAB
cd /tmp/$LAB
eval "$(/opt/homebrew/bin/brew shellenv)"

PY="$(command -v python3.13 || command -v python3)"
[ -d env ] || "$PY" -m venv env
source env/bin/activate
pip install -q -r requirements.txt
mkdir -p logs

brew services start mongodb-community

python manage.py makemigrations warehouse
python manage.py migrate
python manage.py collectstatic --noinput -v 0

rm -f "$(brew --prefix)"/etc/nginx/servers/lr*.conf "$(brew --prefix)"/etc/nginx/servers/shop*.conf "$(brew --prefix)"/etc/nginx/servers/wms*.conf
cp nginx/$LAB.conf "$(brew --prefix)/etc/nginx/servers/$LAB.conf"
nginx -t
brew services restart nginx

supervisorctl -c supervisord.conf shutdown >/dev/null 2>&1 || true
sleep 1
supervisord -c supervisord.conf
sleep 2
supervisorctl -c supervisord.conf status

echo
echo "Готово: http://djangoproject:9000"
open http://djangoproject:9000
