#!/bin/sh
# does not yet perform key binding, which hence has to performed manually

DIR = ~/.YubiGuard
mkidr $DIR && cd $DIR
wget --inet4-only github.com/bfelder/YubiGuard/zipball/master
tar -xzvf master.zip
rm -f master.zip
sudo chmod +x YubiGuard.py
sudo chmod +x YubiGuard_trigger.sh

cat > /etc/init/myjob.conf << EOF
description     "YubiGuard"
start on startup
task
exec /path/to/my/script.sh
EOF

./YubiGuard.py
