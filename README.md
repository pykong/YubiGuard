# YubiGuard - Version 0.1
Python script to prevent accidental triggering of YubiKeys on Linux.

The script uses the xinput command to identify and control the output of YubiKeys:
xinput list
xinput --enable <id>
xinput --disable <id>


Advantages over YubiSwitch:
- No root privilege required to run!
- No unintended output release after reactivation, if you pressed your YubiKey while blocked!
- Can handle more than one YubiKey.
- Timeout which locks off YubiKey after 5 seconds.
- Automatically locking after YubiKey has been triggered.
- Shows notifications to inform about activation status of YubiKey(s).

How to use:
- Download script. Run it or better even make it startup application.
- Install zmq: sudo pip install zmq
- Bind the following command to key combination of your choice (e.g. Super + y):  m="ENABLE" && echo -e $(printf '\\x01\\x00\\x%02x\\x00%s' $(( ${#m})) "$m") | nc -q1 localhost 5555
- Triggering the script will unblock YubiKey. After activation of your YubiKey or after timeout, YubiKey output will again be blocked. 


Tested on:
- Xubuntu 15.10 (Wily Werewolf)

FAQ:
Q: The LED of my YubiKey is still active. Does this mean the script is not working?
A: No. LEDs will continue to blink, despite YubiKey output being blocked as intended.

Known or potential bugs:
- Script does not yet come with handling of exit procedure, hence any changes of xinput will remain after the script's execution.
- Potentially adding USB devices or relocating them to a different port my change their xinput id, thereby rendering them potentially blocked.


Planned:
- add panel icon to show activation status and allow switching ON/OFF via mouse click. 
