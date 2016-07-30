#!/bin/sh

# run this script:
# wget --inet4-only  github.com/bfelder/YubiLock/edit/master/YubiLock_installer.sh 
#&& sudo chmod +x ./YubiLock_installer.sh
#&& ./YubiLock_installer.sh
#&& rm -f ./YubiLock_installer.sh


DIR = ~/.YubiLock/
 PATH2 = ~/.YubiLock/YubiLock.py
mkidr $DIR && cd $DIR
wget --inet4-only github.com/bfelder/YubiLock/zipball/master
tar -xzvf master.zip
rm -f master.zip
sudo chmod +x YubiLock.py

sudo pip install python-xlib

cat > /etc/init/myjob.conf << EOF
description     "YubiLock"
start on startup
task
exec ~/.YubiLock/YubiLock.py
EOF

nohup ./YubiGuard.py > /dev/null 2>&1&&

exit
