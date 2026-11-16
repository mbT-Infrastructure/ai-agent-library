# On-device recipes (adb)

## Read a screen, then act on a label

```bash
scripts/ui.py --serial <serial> dump --file ui1.xml
scripts/ui.py --serial <serial> find 'Settings'
scripts/ui.py --serial <serial> tap 'Settings' 10 --expect 'Wi-Fi'
scripts/ui.py --serial <serial> wait 'Connected'
scripts/ui.py --serial <serial> gone 'Loading'
scripts/ui.py --serial <serial> parse ui1.xml --match 'id/row'
```

`dump` prints one parsed node per line and makes up to three `uiautomator dump` attempts;
`--clickable` also shows icon-only controls, `--file ui1.xml` keeps a snapshot that `parse ui1.xml`
reads back. `tap` re-dumps, taps the match or its clickable ancestor and exits 1 with `NO CHANGE`
when the screen did not change; `--expect` is the real assertion (the bare signature diff is only a
heuristic), a marker already on screen does not prove the tap, and TIMEOUT is only allowed with it.
`wait`/`gone` poll full dumps (~3.1 s per attempt, default 15 s) for actions `ui.py` does not drive.

## Evidence

```bash
adb -s <serial> exec-out screencap -p > screenshot.png
adb -s <serial> shell logcat -d -s SomeTag:V # one tag, current buffer
adb -s <serial> shell logcat -d --pid="$(adb -s <serial> shell pidof <pkg>)" # app only
adb -s <serial> shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' # foreground app
```

## Device state to change and restore

```bash
adb -s <serial> shell settings get system accelerometer_rotation   # 1 = auto-rotate
adb -s <serial> shell settings get system user_rotation            # locked angle, if any
adb -s <serial> shell cmd uimode night                             # prints the current setting
adb -s <serial> shell wm user-rotation lock <n>                    # 0/1/2/3 = 0°/90°/180°/270°
adb -s <serial> shell cmd uimode night yes                         # yes, no or auto
```

Read the values first and ask the user before changing anything: rotation and night mode change the
user's phone, not just the app. In cleanup, `wm user-rotation free` only re-enables auto-rotate; if
the phone was locked to an angle, restore that angle instead with `wm user-rotation lock <n>`. Night
mode restores the same way: `cmd uimode night <value you read>`.
