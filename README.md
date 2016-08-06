# YubiGuard

Python script to protect against accidental triggering of YubiKeys on Linux.

Most recent version: 0.9


## Advantages over YubiSwitch:
1. **No root privilege required to run!**
2. **No unintended output release after reactivation, if you pressed your YubiKey while locked!**
3. Detects YubiKeys automatically, no need to hardcode ids manually.
4. Can handle multiple YubiKeys concurrently.
5. Timeout which locks off YubiKey after 5 seconds.
6. Automatically locking after YubiKey has been triggered.
7. Panel indicator showing the activation status of YubiKey(s).

## Installation & Setup
[...]
### Binding Key Code

### Requirements:
- xinput (installed on most Linux distributions by default)
- pyzmq

```
sudo pip install pyzmq
```
- gir1.2-gtk-3.0
- gir1.2-appindicator3

## Usage:
- YubiLock locks output from all inserted YubiKeys by default.
- the locked state is indicated in the panel by the default icon.
- simply Triggering via key combination (e.g.: super + y) will unlock YubiKey.
- in the unlocked state the icon changes to green.
- after triggering your YubiKey or after timeout, YubiKey will again be locked with the icon reverting back to default
- while no YubiKeys are inserted, the panel indicator will be darkened.

## FAQ:
**_Q:_** The LED of my YubiKey is still active. Does this mean the script is not working?
**_A:_** No. LEDs will continue to blink, despite YubiKey output being blocked as intended.

**_Q:_** How does YubiLock actiavte and deactivate YubiKeys?
**_A:_** YubiLock uses the xinput command to identify and control the output of YubiKeys. Namely:
_xinput list_, _xinput --enable <id>_, _xinput --disable <id>_ and _xinput test <id>_.

## Tested on:
### Linux Distributions (all 64-bit):
- Xubuntu 15.10 (Wily Werewolf)
- Xubuntu 16.04 (Xenial Xerus)
- Elementary OS 0.4
- Fedora 24
- Linux Mint 18 (Cinnamon)
- Manjaro Linux 15.09
- Ubuntu 16.04

### Not working on (all 64-bit):
- Debian 8.5 (Jessie)
- OpenSUSE 42.1
- Solus 1.2
- Mageia 5

(Those distros are not working as xinput is not installed: "xinput: command not found".
One might get YubiGuard to run with additional work though.)

### YubiKey models:
- YubiKey 4 Nano
- YubiKey NEO
- YubiKey II

## Credits_
- yubico generously provided additional YubiKey models for testing
- Stefaan Lippens' asynchronous stdout pipe allowed for an non-blocking way to monitor YubiKey output:
stefaanlippens.net/python-asynchronous-subprocess-pipe-reading

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

### v 0.7
- switched back from KeyEventListener to ZmqListener, as the former interfered with YubiKey release (see issue)

### v 0.8
- changed name back to YubiGuard, as two other GitHub projects are already titled YubiLock
- updated icons
- minor rectifivation of code

### v 0.9
- YubiGuard.py itself is now used for triggering, when run with comman line paramater '-t': yg_trigger.sh is deprecated therefore
- fixed minor bug preventing exit when no keys were inserted
