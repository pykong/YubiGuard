Installation:

Run the following shell command to install:

wget --inet4-only github.com/bfelder/YubiLock/edit/master/YubiLock_installer.sh && sudo chmod +x ./YubiLock_installer.sh && ./YubiLock_installer.sh && rm -f ./YubiLock_installer.sh

How to use:

Simply Triggering via key combination (default: super + y) will unlock YubiKey.
After output from your YubiKey or after timeout, YubiKey output will again be blocked.
How to customize:

open settings.ini (default path: ~/.YubiLock/)
you may specify timeout in seconds
you may also specify your own key code for triggering YubiLock
to get a comprehensive list of all key codes run: xmodmap -pke
edit KEY_CODE option regardingly
