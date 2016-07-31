## How to use:
- Simply Triggering via key combination (default: ctrl_left + y) will unlock YubiKey.
- After output from your YubiKey or after timeout, YubiKey output will again be blocked.

## How to customize:
- open settings.ini (default path: ~/.YubiLock/)

### Timeout:
- you may specify timeout in seconds under the TIMEOUT option

### Key codes:
- to get a comprehensive list of all key codes run: xmodmap -pke
- pick the numerical key codes that correspond to the key combination you desire
- one or more keys can be selected
- not all keycodes work or are recommended, e.g. "super + y" will print out an additional "y"
- edit KEY_CODE option regardingly, with the keycodes separated by comma

### Finally:
- save settings.ini
- restart YubiLock for the changes to take effect
