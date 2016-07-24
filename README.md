# YubiLock

Python script to prevent accidental triggering of YubiKeys on Linux.

Most recent version: 0.3

The script uses the xinput command to identify and control the output of YubiKeys:
xinput list
xinput --enable <id>
xinput --disable <id>


## Advantages over YubiSwitch:
1. No root privilege required to run!
2. No unintended output release after reactivation, if you pressed your YubiKey while blocked!
3. Can handle more than one YubiKey.
4. Timeout which locks off YubiKey after 5 seconds.
5. Automatically locking after YubiKey has been triggered.
6. Shows notifications to inform about activation status of YubiKey(s).

## How to use:
- Download script. Run it or better even make it startup application.
- Install zmq: sudo pip install zmq
- Bind the triggering script trigger_YL.sh command to key combination of your choice (e.g. Super + y):  
(Note for some reason it might be neccessary to specify your shell within the shebang. For example .../bash instead of .../sh.)
- Triggering the script will unblock YubiKey. After activation of your YubiKey or after timeout, YubiKey output will again be blocked. 


## Tested on:
- Xubuntu 15.10 (Wily Werewolf)
- Xubuntu 16.04 (Xenial Xerus)

## FAQ:
_Q:_ The LED of my YubiKey is still active. Does this mean the script is not working?
_A:_ No. LEDs will continue to blink, despite YubiKey output being blocked as intended.

## Known or potential bugs:
- Script does not yet come with handling of exit procedure, hence any changes of xinput will remain after the script's execution.

## Changelog:
### v 0.2:
- renamed to YubiLock, as this name better portrays the function
- instead of text notificaions, now descriptive icons are displayed
- in case of changing xinput ids (e.g. devices are switched) old ids will be automatically activated

### v 0.3
- beautified icons
- set working dir, to always allow relative import of icons
- now preventing overtriggering when hitting key combinations in short succession
