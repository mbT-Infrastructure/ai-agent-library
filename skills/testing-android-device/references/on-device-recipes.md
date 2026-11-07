# On-device recipes (adb)

## Robust ui dump (retry + staleness guard)

```
adb -s <serial> shell input tap <x> <y>; sleep 2
for i in 1 2 3; do
  adb -s <serial> shell uiautomator dump /sdcard/ui.xml 2>/dev/null | grep -q "dumped to" && break
  sleep 1
done
adb -s <serial> shell cat /sdcard/ui.xml | <skill-dir>/scripts/parse_uidump.py
```

Use `parse_uidump.py --clickable` when icon buttons have no text/desc, or `--all` to inspect every
node.

Pass an explicit dump path and keep several snapshots (ui.xml, ui2.xml,
ui3.xml) to compare screen states. Always confirm a text marker unique to
the expected screen before tapping coordinates from a dump — early dumps
can be stale or empty.

## Evidence + logs

```
adb -s <serial> logcat -c                 # before the action
# ... drive the UI ...
adb -s <serial> shell screencap -p /sdcard/evidence.png
adb -s <serial> pull /sdcard/evidence.png .
adb -s <serial> logcat -d -s SomeTag:V OtherTag:E
adb -s <serial> shell rm -f /sdcard/ui*.xml /sdcard/evidence.png   # cleanup
```
