---
name: testing-android-device
description: Use for testing Android apps on real devices via adb.
---

# Android On-Device Testing

Verify app behavior on real hardware: install over wireless adb, drive the UI without touching it,
read device state, capture evidence.

## When to Use

- Testing of non-trivial Android app changes
- Reproducing issues that only show on real hardware
- Gathering evidence (screenshots, logcat, dumpsys) for a bug report

## Workflow

1. If you have no assigned dev phone: ask the user for the hostname of the device to use
2. Connect and install
    - `adb connect "$(resolve-dns.sh --name <hostname>):5555"`
    - `adb -s <serial> install -r app/build/outputs/apk/debug/app-debug.apk`
    - `adb -s <serial> reverse tcp:<port> tcp:<port>` when the app needs a host-side service
3. Check availability:
    - Screen on and device unlocked:
      `adb shell dumpsys trust | sed --silent 's/.*\(deviceLocked=.\),.*/\1/p'`. If locked, ask the
      user to unlock.
4. Launch and drive the UI, Test and Verify
    - `adb -s <serial> shell am force-stop <pkg> &&`
      `adb -s <serial> shell am start -n <pkg>/.MainActivity` for a clean start
    - `adb -s <serial> shell input tap <x> <y>`, `adb -s <serial> shell input keyevent 4` (back) for
      interaction.
    - Get element coordinates from `uiautomator dump`, parsed by `scripts/parse_uidump.py`. Use
      `--clickable` for icon-only controls and `--all` for every node.
5. Clean up
    - Delete temp files on the phone.
    - Close the app: `adb -s <serial> shell am force-stop <pkg>`
    - Turn screen off: `adb -s <serial> shell input keyevent 223`

Batch drive → sleep → dump → parse inside one terminal call.

Ready to use command recipes from `references/on-device-recipes.md`.

## Wireless-ADB

Port `5555` is the default port and also used as placeholder for different adb ports. Android 11+
may need `adb pair` first. When `adb connect` refuses, diagnose in this order — don't retry blindly:

1. `ping <ip>`: not reachable → device off or wrong IP (DHCP).
    - If it fails ask the user for the correct address or hostname
2. `timeout 2 bash -c 'echo > /dev/tcp/<ip>/5555'`: fails → port closed but ping OK
    - Ask the user if wireless ADB is off, pairing is needed or the port is different.

## Device problems and configuration

If any of these problems occur, these settings or actions may help. Ask the user before changing any
setting:

- Features fail silently because of missing runtime permissions:
    - Install with `-g` or grant explicitly with
      `adb -s <serial> shell pm grant <pkg> <permission>`.
- The screen sleeps mid-session
    - Check `adb -s <serial> shell settings get system screen_off_timeout`. If it is short ask the
      user for permission to raise it to 30 min. Never use `svc power stayon`.
    - Run
      `adb -s <serial> shell input keyevent KEYCODE_WAKEUP && adb shell dumpsys trust | sed --silent 's/.*\(deviceLocked=.\),.*/\1/p'`
      to rewake the screen and check if unlocked.
- Dialogs shift under the soft keyboard
    - after `input text`, re-dump and recompute button coordinates before tapping. Coordinates from
      the pre-typing dump now may land in the keyboard.

## Project specific guide

`./.agent/testing-android-device/` is the project specific folder for Android on-device testing with
`./.agent/testing-android-device/Readme.md` being the project specific guide extending this guide.
As you go, create, expand or modify the project specific guide and associated files like scripts and
references.
