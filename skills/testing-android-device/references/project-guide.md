# Android on-device testing

Verified: <date> on <device> (<android version>) against <versionName>.

## Device and install
- Serial: <hostname> -> <ip:port>
- Package / activity: <pkg> / <pkg>/.MainActivity
- Build and install: <command>; artifact: <path>
- Permissions to grant: <...>
- Clean state: <reset/seed command>; wipes: <...>

## Driving the app
- Screens: <marker> -> <screen> -> <next action>
- Ambiguous labels: <label> matches <M> nodes, use `--index N` (0-based, N < M)
- Waits and overlays: <marker>; auto-hides after <N> s
- Dead ends: <action> does nothing / exits the app

## Test setup
- Data: <accounts, config>
- Host services: <adb reverse tcp:...>
- Logs: <tags>; app data: <path, when debuggable>

## Not testable here
- <thing> — because <device fact>

## Quirks
- <date>: <quirk> -> <workaround>
