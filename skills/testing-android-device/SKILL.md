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

## Project specific guide

`<project-root>/.agent/guides/testing-android-device.md` is this project's memory for this skill:
device, install command, package and activity, screen markers, quirks. Read it before the first tap.
If it does not exist, create it from this skill's `references/project-guide.md`.

- Fill only what this project needs beyond this skill. Do not repeat content of this skill or
  `ui.py --help`.
- Replace every `<...>` in the template with the value and delete sections that do not apply.
- Add a dated line when a step costs a retry (e.g. a `NO CHANGE` or a timeout) and correct wrong
  entries instead of appending a second version.

## Workflow

1. If you have no assigned dev phone: ask the user for the hostname of the device to use
2. Connect and install
    - `adb connect "$(resolve-dns.sh --name <hostname>):5555"`
    - `adb -s <serial> install -r <apk>`
    - `adb -s <serial> reverse tcp:<port> tcp:<port>` when the app needs a host-side service
3. Check availability
    - Screen on and device unlocked:
      `adb -s <serial> shell dumpsys trust | sed --silent 's/.*\Delete(deviceLocked=.\),.*/\1/p'`.
      If locked, ask the user to unlock.
4. Launch and drive the UI, test and verify
    - `adb -s <serial> shell 'am force-stop <pkg> && am start -n <pkg>/<activity>'` for a clean
      start
    - `adb -s <serial> shell input keyevent 4` (back) to navigate.
    - Never tap a bare coordinate: `scripts/ui.py --serial <serial> find REGEX` shows the match
      (`--clickable` for icon-only controls); `scripts/ui.py --serial <serial> tap REGEX` taps the
      match or its clickable ancestor and exits 1 with `NO CHANGE` when the screen did not change.
    - Assert after every state-changing action with `--expect`:
      `scripts/ui.py --serial <serial> tap REGEX --expect REGEX` polls for the marker; for back or
      app start use `scripts/ui.py --serial <serial> wait REGEX` /
      `scripts/ui.py --serial <serial> gone REGEX`.
    - Type into a field: `scripts/ui.py --serial <serial> type REGEX TEXT [--clear] [--enter]` (taps
      the field, optionally clears it, types and verifies the text).
    - Inspect a screen with `scripts/ui.py --serial <serial> dump` (`--all`, `--file` or `--raw`) or
      `scripts/ui.py --serial <serial> parse` a saved dump; `scripts/ui.py --help` lists every
      command and flag.
    - If the build is debuggable, use the app's data file (`run-as <pkg>`) to confirm what the UI
      shows.
5. Clean up
    - Delete temp files on the phone.
    - Restore changed device state (see "Device state to change and restore" in
      `references/on-device-recipes.md`).
    - Close the app: `adb -s <serial> shell am force-stop <pkg>`
    - Turn screen off: `adb -s <serial> shell input keyevent 223`

Command recipes live in `references/on-device-recipes.md`. `sed --silent 's/^## //p'` on it lists
the sections.

## Wireless-ADB

Port `5555` is the default. Substitute the device's port where it differs. Android 11+ may need
`adb pair` first. When `adb connect` refuses, diagnose in this order and don't retry blindly:

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
    - Run `adb -s <serial> shell input keyevent KEYCODE_WAKEUP`, then the `dumpsys trust` check from
      step 3, to rewake the screen and check whether it is unlocked.
- The soft keyboard hides the target
    - Check `adb -s <serial> shell dumpsys input_method | grep mInputShown` and dismiss the keyboard
      with `adb -s <serial> shell input keyevent 4`.
