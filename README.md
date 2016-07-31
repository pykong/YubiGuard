# YubiLock

Python script to prevent accidental triggering of YubiKeys on Linux.

Most recent version: 0.6


## Advantages over YubiSwitch:
1. **No root privilege required to run!**
2. **No unintended output release after reactivation, if you pressed your YubiKey while locked!**
3. Can handle multiple YubiKeys concurrently.
4. Timeout which locks off YubiKey after 5 seconds.
5. Automatically locking after YubiKey has been triggered.
6. Panel indicator showing the activation status of YubiKey(s).

## Installation:
Run the following shell command to install (-- INSTALLER SCRIPT NOT TESTED YET --):


### Requirements:
-python-xlib
    sudo pip install python-xlib)

## Usage:
- YubiLock locks output from all inserted YubiKeys by default.
- the locked state is indicated in the panel by the default icon:
- simply Triggering via key combination (default: ctrl_left + y) will unlock YubiKey.
- in the unlocked state the icon changes to green: 
- after triggering your YubiKey or after timeout, YubiKey will again be locked with the icon reverting back to default
- while no YubiKeys are inserted, the panel indicator will be darkened: 





## How to customize:
- open settings.ini (default path: ~/.YubiLock/)

### Customize timeout:
- you may specify timeout in seconds under the TIMEOUT option

### Customize key codes:
- to get a comprehensive list of all key codes run: xmodmap -pke
- pick the numerical key codes that correspond to the key combination you desire
- one or more keys can be selected
- not all keycodes work or are recommended, e.g. "super + y" will print out an additional "y"
- note that system key bindings will not be overridden, so be careful not to choose one already in use
- edit KEY_CODE option regardingly, with the keycodes separated by comma

### Finally:
- save settings.ini
- restart YubiLock for the changes to take effect


## Tested on:
### Linux Distributions:
- Xubuntu 15.10 (Wily Werewolf)
- Xubuntu 16.04 (Xenial Xerus)

### YubiKey models:
- YubiKey 4 Nano

### Keyboard Layout:
- German (QWERTZU)

## FAQ:
**_Q:_** The LED of my YubiKey is still active. Does this mean the script is not working?
**_A:_** No. LEDs will continue to blink, despite YubiKey output being blocked as intended.

**_Q:_** How does YubiLock actiavte and deactivate YubiKeys?
**_A:_** YubiLock uses the xinput command to identify and control the output of YubiKeys. Namely:
_xinput list_, _xinput --enable <id>_, _xinput --disable <id>_ and _xinput test <id>_.


## Changelog:
### v 0.2:
- renamed to YubiLock, as this name better portrays the function
- instead of text notificaions, now descriptive icons are displayed
- in case of changing xinput ids (e.g. devices are switched) old ids will be automatically activated

### v 0.3
- beautified icons
- set working dir, to always allow relative import of icons
- now preventing overtriggering when hitting key combinations in short succession

### v 0.4
- added exit handler, which will reactivate YubiKeys after script has exited

### v 0.5
- code rectified
- introduced missing thread locking

### v 0.6 (major update)
- added a Panel Indicator (replacing notification of LOCK/UNLOCK)
- major rectification of code
- switched from thread based concurrency to process based for superb responsiveness
- added key event listener, replacing triggering via external script over zmq
- added settings.ini to grant user to customize time out and triggering key combination
- eliminated minor bugs which led to laggy or unreliable unlocking
