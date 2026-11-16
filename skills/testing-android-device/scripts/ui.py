#!/usr/bin/env python3
"""Label-addressed UI actions on an Android device over adb.

One stdlib-only file that keeps the node line format and stdout/stderr contract of the two
superseded scripts. A dump is trusted because uiautomator wrote it; parse FILE trusts the caller.
"""
import argparse
import collections
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ElementTree  # nosemgrep: trusted device dump

EXIT_SUCCESS, EXIT_ERROR = 0, 1
EXIT_DEPENDENCY, EXIT_ARGUMENT = 10, 13
EXIT_FILE, EXIT_MISSING = 14, 15
FILTERS = ("text", "content-desc", "resource-id")
BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
SIZE = re.compile(r"\s*(Physical|Override) size: (\d+)x(\d+)")
END = "</hierarchy>"
POLL_TIMEOUT, EXPECT_TIMEOUT = 15, 10

EPILOG = """\
Commands:
  dump  [--file PATH] [--raw] [--all | --clickable]
  find  REGEX [--index N] [--all | --clickable]
  tap   REGEX [TIMEOUT] [--index N] [--expect REGEX] [--interval S]
  type  REGEX TEXT [--clear] [--enter] [--index N]
  wait  REGEX [TIMEOUT] [--interval S]
  gone  REGEX [TIMEOUT] [--interval S]
  parse [FILE] [--match REGEX] [--all | --clickable]    FILE: "-" or omitted is stdin
Global options, anywhere before "--":
  --serial SERIAL  device serial, else ANDROID_SERIAL, else the one device of "adb devices"
  --literal        every REGEX, --match and --expect is a fixed string, not a regex
  --               end of the globals; a following pattern may start with "-"
Output: stdout is the result only (node lines, raw XML, "changed", "NO CHANGE", "gone", "typed");
stderr the detail lines and one "Error: " per failure. --index N is 0-based; --file writes
atomically after validating the directory. tap compares the multiset of (class, text, content-desc,
resource-id, checked, clickable, bounds) over labeled, clickable or checkable nodes, so a reordered
screen is "NO CHANGE" and a pre-present --expect marker only proves the tap when the screen
changed. type sends MOVE_END and one DEL per old character with --clear, then verifies (old + TEXT,
masked by length) before "typed"; TEXT is printable ASCII, spaces become %s, a literal %s becomes a
space, multiple keycodes need Android 10+. TIMEOUT is a lower bound per dump; coordinates beyond
"wm size" are rejected, without it only negative ones.
Exit codes: 0 success, 1 failed assertion, device/dump/write error or SIGINT/SIGTERM, 10 missing
dependency, 13 invalid arguments or regex, 14 file missing or empty, 15 missing argument.
11, 12 and 16 are not used: no lock file, no root requirement, --file overwrites.
"""


class Failure(Exception):
    """An error together with the process exit code it maps to."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


class UsageParser(argparse.ArgumentParser):
    """Argument parser that raises Failure with the documented exit codes."""

    def error(self, message):
        missing = "expected one argument" in message or "arguments are required" in message
        raise Failure(EXIT_MISSING if missing else EXIT_ARGUMENT, message)


def require(value, message):
    if not value:
        raise Failure(EXIT_MISSING, message)
    return value


def pattern(text, literal=False):
    """Compile TEXT, escaped when LITERAL; a missing or empty REGEX is a missing argument."""
    require(text, "the following arguments are required: REGEX")
    try:
        return re.compile(re.escape(text) if literal else text)
    except re.error as error:
        raise Failure(EXIT_ARGUMENT, f"invalid regex: {error}") from None


def integer_type(label, allow_zero):
    def convert(text):
        require(text, f"Missing value for {label}.")
        if not text.isdecimal() or len(text) > 6 or (not allow_zero and int(text) == 0):
            kind = "a non-negative integer" if allow_zero else "a positive integer"
            raise argparse.ArgumentTypeError(f'{label} must be {kind} (max 6 digits): "{text}"')
        return int(text)
    return convert


def bounds_rect(value):
    match = BOUNDS.fullmatch(value or "")
    return tuple(int(group) for group in match.groups()) if match else None


def format_node(node, tap_center=None):
    """Format one node as the documented key=value line, with an optional tap=x,y suffix."""
    rect = bounds_rect(node.get("bounds", ""))
    position, bounds = ("-", '""') if rect is None else (
        f"{(rect[0] + rect[2]) // 2},{(rect[1] + rect[3]) // 2}", node.get("bounds", ""))
    text, desc, resource_id = (json.dumps(node.get(name, ""), ensure_ascii=False)
                               for name in FILTERS)
    line = (f"{text} | desc={desc} | id={resource_id} | clickable={node.get('clickable', '')}"
            f" | center={position} | bounds={bounds}")
    return line if tap_center is None else f"{line} tap={tap_center}"


def select(root, match=None, everything=False, clickable=False):
    """Yield the nodes of ROOT that the selection rules keep, in document order."""
    for node in root.iter("node"):
        labeled = bool(node.get("text", "").strip() or node.get("content-desc", "").strip())
        extra = (not labeled and node.get("clickable") == "true"
                 and bool(node.get("resource-id", "").strip()))
        selected = everything or labeled or ((match or clickable) and extra)
        if selected and (match is None or any(match.search(node.get(n, "")) for n in FILTERS)):
            yield node


def parse_xml(text):
    """Return the root element of a dump, ignoring everything after "</hierarchy>"."""
    end = text.rfind(END)
    try:
        return ElementTree.fromstring(text if end < 0 else text[:end + len(END)])  # nosemgrep
    except ElementTree.ParseError as error:
        raise Failure(EXIT_ERROR, f"invalid XML: {error}") from None


def ancestors(item, parents):
    """Return ITEM and its ancestors up to the root of its dump."""
    lineage = [item]
    while lineage[-1] in parents:
        lineage.append(parents[lineage[-1]])
    return lineage


def tap_target(node, root, description):
    """Return the centre of the first usable candidate: the node, else its clickable ancestors."""
    parents = {child: parent for parent in root.iter() for child in parent}
    lineage = ancestors(node, parents)[1:]
    chain = [node] if node.get("clickable") == "true" else []
    chain += [item for item in lineage if item.get("clickable") == "true"] + [node, *lineage]
    for candidate in chain:
        rect = bounds_rect(candidate.get("bounds", ""))
        if rect is not None and rect[2] > rect[0] and rect[3] > rect[1]:
            return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
    raise Failure(EXIT_ERROR, f"no usable tap point for {description} (no positive-area bounds)")


def send_tap(device, x, y, prefix="tap"):
    """Reject an off-screen (X, Y) and tap it; PREFIX names the command in the warning."""
    size = device.screen_size()
    if size is None:
        print(f"{prefix}: screen size unavailable, only negative coordinates are checked",
              file=sys.stderr)
    if x < 0 or y < 0 or (size is not None and (x >= size[0] or y >= size[1])):
        raise Failure(EXIT_ERROR, f"node is off-screen at {x},{y}.")
    if device.run(["shell", f"input tap {x} {y}"])[0] != 0:
        raise Failure(EXIT_ERROR, "adb input tap failed.")


def remote_text(text):
    """Return TEXT as one shell word for `input text`, single-quoted and spaces as %s."""
    return "'" + text.replace("'", "'\\''").replace(" ", "%s") + "'"


def path(item, parents):
    """Return the (class, id, clickable) path from the root down to ITEM."""
    return tuple((part.get("class", ""), part.get("resource-id", ""), part.get("clickable", ""))
                 for part in reversed(ancestors(item, parents)))


def field_after(root, before, node):
    """Return the focused node of ROOT on NODE's tap path, else the node with the same id.

    Bounds move with the keyboard, so the chain is compared by path; focus elsewhere fails."""
    own = path(node, {child: parent for parent in before.iter() for child in parent})
    cut = max((index + 1 for index, part in enumerate(own) if part[2] == "true"), default=len(own))
    parents = {child: parent for parent in root.iter() for child in parent}
    for item in (item for item in root.iter("node") if item.get("focused") == "true"):
        focused = path(item, parents)
        if focused[:cut] == own[:cut] or own[:len(focused)] == focused:
            return item
    return next((item for item in root.iter("node")
                 if item.get("resource-id") == node.get("resource-id", "") != ""), None)


def signature(root):
    """Return the multiset of (class, text, desc, id, checked, clickable, bounds) of ROOT."""
    state = ((node.get("class", ""), node.get("text", ""), node.get("content-desc", ""),
              node.get("resource-id", ""), node.get("checked", ""), node.get("clickable", ""),
              node.get("bounds", "")) for node in root.iter("node")
             if node.get("text", "").strip() or node.get("content-desc", "").strip()
             or node.get("clickable") == "true" or node.get("checkable") == "true")
    return collections.Counter(state)


def read_source(path):
    """Return the dump text from PATH, or stdin for None or "-"; 14 when unreadable."""
    if path not in (None, "-"):
        try:
            with open(path, encoding="utf-8", errors="replace") as file:
                text = file.read()
        except OSError as error:
            raise Failure(EXIT_FILE, f'cannot read "{path}": {error.strerror or error}') from None
        if not text:
            raise Failure(EXIT_FILE, f'"{path}" is empty')
        return text
    if sys.stdin is None:
        raise Failure(EXIT_ERROR, "cannot read stdin: stdin is closed")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # dumps are UTF-8
    try:
        return sys.stdin.read()
    except (OSError, ValueError) as error:
        raise Failure(EXIT_ERROR, f"cannot read stdin: {error}") from None


def command_parse(arguments, literal):
    match = None if arguments.match is None else pattern(arguments.match, literal)
    source = parse_xml(read_source(arguments.file))
    for node in select(source, match, arguments.all_nodes, arguments.clickable):
        print(format_node(node))
    return EXIT_SUCCESS


class Device:
    """One adb target: command resolution, serial selection, dumps and screen size."""

    serial = ""  # the device listing must run without -s

    def __init__(self, serial):
        try:
            self.command = shlex.split(os.environ.get("ADB", "adb"))
        except ValueError as error:
            raise Failure(EXIT_ARGUMENT, f"invalid ADB command: {error}") from None
        if len(self.command) > 1 and shutil.which(os.environ.get("ADB", "")):
            self.command = [os.environ["ADB"]]  # a plain path that contains spaces
        name = self.command[0] if self.command else "adb"
        if not self.command or shutil.which(name) is None:
            raise Failure(EXIT_DEPENDENCY, f'"{name}" is missing!')
        self.remote = f"/sdcard/ui.py-{uuid.uuid4()}.xml"

        def handle_interrupt(signum, frame):
            """Remove the remote dump, report one line and exit 1; dump's finally repeats the rm."""
            self.run(["shell", f"rm -f '{self.remote}'"])
            print("Error: interrupted.", file=sys.stderr)
            sys.exit(EXIT_ERROR)

        for name in (signal.SIGINT, signal.SIGTERM):
            signal.signal(name, handle_interrupt)
        self.serial = self.select_serial(serial)
        if self.run(["get-state"])[0] != 0:
            raise Failure(EXIT_ERROR, f'device "{self.serial}" not connected.')

    def run(self, arguments, timeout=30):
        command = list(self.command) + (["-s", self.serial] if self.serial else [])
        try:
            result = subprocess.run(command + arguments, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            return EXIT_ERROR, "", f"timed out after {timeout}s"
        return result.returncode, result.stdout, result.stderr

    def select_serial(self, serial):
        """Return SERIAL, ANDROID_SERIAL or the single device that adb lists as "device"."""
        if serial or os.environ.get("ANDROID_SERIAL"):
            return serial or os.environ["ANDROID_SERIAL"]
        connected = [fields[0] for line in self.run(["devices"])[1].splitlines()
                     if (fields := line.split())[1:2] == ["device"]]
        if not connected:
            raise Failure(EXIT_ERROR, "No device connected. Pass --serial SERIAL.")
        if len(connected) > 1:
            listed = "\n".join(f"    {item}" for item in connected)
            raise Failure(EXIT_ERROR, "Multiple devices connected, pass --serial SERIAL or set "
                                      f"ANDROID_SERIAL:\n{listed}")
        return connected[0]

    def dump(self):
        """Return a dump that contains "</hierarchy>", retrying three times."""
        remote = f"rm -f '{self.remote}'; uiautomator dump '{self.remote}' >/dev/null 2>&1;"
        try:
            error_line = ""
            for attempt in (1, 2, 3):
                _, output, error = self.run(["shell", f"{remote} cat '{self.remote}' 2>/dev/null"])
                if output.strip() and END in output:
                    return output
                print(f"dump: attempt {attempt} failed", file=sys.stderr)
                error_line = error.strip().splitlines()[0] if error.strip() else ""
            raise Failure(EXIT_ERROR, f"uiautomator dump failed: {error_line}" if error_line else
                          "uiautomator dump failed (screen off or locked?)")
        finally:
            self.run(["shell", f"rm -f '{self.remote}'"])

    def screen_size(self):
        """Return (width, height) from the last "Override size:" else "Physical size:"."""
        code, output, _ = self.run(["shell", "wm size"])
        sizes = {match.group(1): (int(match.group(2)), int(match.group(3)))
                 for match in map(SIZE.match, output.splitlines()) if match} if code == 0 else {}
        return sizes.get("Override") or sizes.get("Physical")


def validate_target(path):
    """Return the normalized --file target, validated before any dump happens."""
    require(path, "Missing value for --file PATH.")
    if path.startswith("-"):
        raise Failure(EXIT_ARGUMENT, f'Invalid --file PATH, must not start with "-": "{path}"')
    directory = os.path.dirname(path) or "."
    if not os.path.isdir(directory):
        raise Failure(EXIT_FILE, f'Output directory does not exist: "{directory}"')
    if not os.access(directory, os.W_OK):
        raise Failure(EXIT_ERROR, f'Output directory is not writable: "{directory}"')
    target = os.path.join(directory, os.path.basename(path))
    if os.path.isdir(target):
        raise Failure(EXIT_ERROR, f'Output path is a directory: "{target}"')
    return target


def write_file(path, text):
    """Write TEXT to PATH through a hidden temporary file and an atomic replace."""
    temporary = os.path.join(os.path.dirname(path) or ".", f".ui.py-{uuid.uuid4()}.tmp")
    try:
        with open(temporary, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temporary, path)
    except OSError as error:
        raise Failure(EXIT_ERROR, f'Cannot write "{path}": {error.strerror or error}') from None
    finally:
        if os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass


def command_dump(device, arguments):
    """Print the nodes of a fresh dump; --raw prints the XML, --file writes it."""
    if arguments.raw and (arguments.clickable or arguments.all_nodes):
        raise Failure(EXIT_ARGUMENT, "--raw cannot be combined with --clickable or --all.")
    target = None if arguments.file is None else validate_target(arguments.file)
    output = device.dump()
    if target is not None:
        write_file(target, output)
    root = parse_xml(output)
    if arguments.raw:
        sys.stdout.write(output)
        print(f"dump: {len(list(root.iter('node')))} node(s)", file=sys.stderr)
        return EXIT_SUCCESS
    nodes = list(select(root, everything=arguments.all_nodes, clickable=arguments.clickable))
    for node in nodes:
        print(format_node(node))
    print(f"dump: {len(nodes)} node(s)", file=sys.stderr)
    return EXIT_SUCCESS


def command_find(device, arguments, literal):
    match = pattern(arguments.regex, literal)
    nodes = list(select(parse_xml(device.dump()), match, everything=arguments.all_nodes,
                        clickable=arguments.clickable))
    print(f"find: {len(nodes)} match(es) index={arguments.index}", file=sys.stderr)
    if not nodes:
        raise Failure(EXIT_ERROR, f'No matching node for "{arguments.regex}".')
    if arguments.index >= len(nodes):
        raise Failure(EXIT_ERROR,
                      f"Index {arguments.index} out of range ({len(nodes)} match(es)).")
    print(format_node(nodes[arguments.index]))
    return EXIT_SUCCESS


def timing(prefix, verb, elapsed, attempt, timeout):
    if elapsed > timeout:
        return f"{prefix}: {verb} after {elapsed}s, past the {timeout}s timeout"
    return f"{prefix}: {verb} after {elapsed}s (attempt {attempt})"


def poll(device, match, timeout, interval, wanted, missed):
    """Return (root, nodes, elapsed, attempt); root and nodes are None on timeout."""
    start, attempt = time.monotonic(), 0
    while True:
        elapsed = time.monotonic() - start
        if attempt > 0 and elapsed >= timeout:
            return None, None, int(elapsed), attempt
        attempt += 1
        root = parse_xml(device.dump())
        nodes = list(select(root, match))
        elapsed = time.monotonic() - start
        if bool(nodes) is wanted:
            return root, nodes, int(elapsed), attempt
        print(missed.format(attempt=attempt, elapsed=int(elapsed)), file=sys.stderr)
        if interval > 0:
            time.sleep(interval)


def command_poll(device, arguments, literal, wanted):
    """Poll until MATCH appears (WANTED) or disappears, then print nodes or "gone"."""
    match = pattern(arguments.regex, literal)
    timeout, prefix = arguments.timeout or POLL_TIMEOUT, "wait" if wanted else "gone"
    missed = "{}: attempt {{attempt}}, {} after {{elapsed}}s".format(
        prefix, "no match" if wanted else "still present")
    _, nodes, elapsed, attempt = poll(device, match, timeout, arguments.interval, wanted, missed)
    if nodes is None:
        note = " (attempt {})." if wanted else ", node is still present (attempt {})."
        raise Failure(EXIT_ERROR, f"Timed out after {elapsed}s{note.format(attempt)}")
    print("gone" if not wanted else "\n".join(format_node(node) for node in nodes))
    print(timing(prefix, "matched" if wanted else "absent", elapsed, attempt, timeout),
          file=sys.stderr)
    return EXIT_SUCCESS


def command_wait(device, arguments, literal):
    return command_poll(device, arguments, literal, True)


def command_gone(device, arguments, literal):
    return command_poll(device, arguments, literal, False)


def command_tap(device, arguments, literal):
    """Tap the selected node, then verify with --expect or the node-set signature."""
    match = pattern(arguments.regex, literal)
    expect = None if arguments.expect is None else pattern(arguments.expect, literal)
    if arguments.timeout is not None and expect is None:
        raise Failure(EXIT_ARGUMENT, "TIMEOUT requires --expect REGEX.")
    timeout = arguments.timeout or EXPECT_TIMEOUT
    root = parse_xml(device.dump())
    nodes = list(select(root, match))
    if not nodes or arguments.index >= len(nodes):
        print(f"tap: {len(nodes)} match(es) index={arguments.index}", file=sys.stderr)
        raise Failure(EXIT_ERROR, f"Index {arguments.index} out of range ({len(nodes)} match(es))."
                      if nodes else f'No matching node for "{arguments.regex}".')
    node = nodes[arguments.index]
    x, y = tap_target(node, root, f'"{arguments.regex}"')
    print(f"tap: matches={len(nodes)} index={arguments.index} {format_node(node, f'{x},{y}')}",
          file=sys.stderr)
    pre_present = expect is not None and next(select(root, expect), None) is not None
    if pre_present:
        print("tap: expect marker already present before the tap", file=sys.stderr)
    send_tap(device, x, y)
    if expect is None:
        if signature(parse_xml(device.dump())) == signature(root):
            print("NO CHANGE")
            raise Failure(EXIT_ERROR, f'Screen did not change after tapping "{arguments.regex}".')
        print("changed")
        return EXIT_SUCCESS
    after, found, elapsed, attempt = poll(
        device, expect, timeout, arguments.interval, True,
        "tap: expect attempt {attempt}, no match after {elapsed}s")
    if found is None:
        print("NO CHANGE")
        raise Failure(EXIT_ERROR, f'expect "{arguments.expect}" not found after {elapsed}s '
                                  f"(timeout {timeout}s).")
    if pre_present and signature(after) == signature(root):
        print("NO CHANGE")
        raise Failure(EXIT_ERROR, f'expect marker "{arguments.expect}" was already present and '
                                  "the screen did not change after the tap.")
    for node in found:
        print(format_node(node), file=sys.stderr)
    print(timing("tap", "expect matched", elapsed, attempt, timeout), file=sys.stderr)
    print("changed")
    return EXIT_SUCCESS


def command_type(device, arguments, literal):
    """Tap the field that MATCH selects, type TEXT into it and verify the field text."""
    match = pattern(arguments.regex, literal)
    if not arguments.text and not arguments.clear:
        raise Failure(EXIT_MISSING, "the following arguments are required: TEXT")
    text = arguments.text or ""
    if text and not all(" " <= character <= "~" for character in text):
        raise Failure(EXIT_ARGUMENT, "TEXT must be printable ASCII without line breaks: "
                                     f"{json.dumps(text, ensure_ascii=False)}")
    root = parse_xml(device.dump())
    nodes = list(select(root, match, everything=True))
    if not nodes or arguments.index >= len(nodes):
        print(f"type: {len(nodes)} match(es) index={arguments.index}", file=sys.stderr)
        raise Failure(EXIT_ERROR, f"Index {arguments.index} out of range ({len(nodes)} match(es))."
                      if nodes else f'No matching node for "{arguments.regex}".')
    node = nodes[arguments.index]
    old = node.get("text", "")
    x, y = tap_target(node, root, f'"{arguments.regex}"')
    print(f"type: matches={len(nodes)} index={arguments.index} {format_node(node, f'{x},{y}')}",
          file=sys.stderr)
    masked = node.get("password") == "true" or bool(old) and set(old) <= {"•", "*", "●"}
    if masked:  # the pre-dump already tells whether the field masks its value
        print("type: password field, comparing the masked length only", file=sys.stderr)
    send_tap(device, x, y, "type")
    keys = ["123"] + ["67"] * (len(old) if arguments.clear else 0)
    for start in range(0, len(keys), 100):  # 100 keycodes per call keep the argv small
        batch = " ".join(keys[start:start + 100])
        if device.run(["shell", f"input keyevent {batch}"])[0] != 0:
            raise Failure(EXIT_ERROR, "adb input keyevent failed.")
    if text and device.run(["shell", f"input text {remote_text(text)}"])[0] != 0:
        raise Failure(EXIT_ERROR, "adb input text failed.")
    result = field_after(parse_xml(device.dump()), root, node)
    if result is None:
        raise Failure(EXIT_ERROR, "cannot find the field again after typing.")
    expected, shown = ("" if arguments.clear else old) + text, result.get("text", "")
    print(f"type: result {format_node(result)}", file=sys.stderr)
    if masked and len(shown) != len(expected):
        print("NO CHANGE")
        raise Failure(EXIT_ERROR, f"expected {len(expected)} masked character(s), "
                                  f"field shows {len(shown)}.")
    if not masked and shown != expected:
        print("NO CHANGE")
        raise Failure(EXIT_ERROR, f"expected {json.dumps(expected)}, "
                                  f"field shows {json.dumps(shown)}.")
    if arguments.enter:
        if device.run(["shell", "input keyevent 66"])[0] != 0:
            raise Failure(EXIT_ERROR, "adb input keyevent failed.")
        print("type: pressed enter (keyevent 66)", file=sys.stderr)
    print("typed")
    return EXIT_SUCCESS


OPTIONS = {
    "file": ("--file", {"metavar": "PATH"}),
    "raw": ("--raw", {"action": "store_true"}),
    "clickable": ("--clickable", {"action": "store_true"}),
    "all": ("--all", {"dest": "all_nodes", "action": "store_true"}),
    "index": ("--index", {"metavar": "N", "default": 0, "type": integer_type("--index", True)}),
    "interval": ("--interval",
                 {"metavar": "S", "default": 0, "type": integer_type("--interval", True)}),
    "expect": ("--expect", {"metavar": "REGEX"}),
    "match": ("--match", {"metavar": "REGEX"}),
    "clear": ("--clear", {"action": "store_true"}),
    "enter": ("--enter", {"action": "store_true"}),
    "REGEX": ("regex", {"metavar": "REGEX", "nargs": "?"}),
    "TEXT": ("text", {"metavar": "TEXT", "nargs": "?"}),
    "TIMEOUT": ("timeout",
                {"metavar": "TIMEOUT", "nargs": "?", "type": integer_type("TIMEOUT", False)}),
    "FILE": ("file", {"metavar": "FILE", "nargs": "?"}),
}
LAYOUT = (
    ("dump", ("file", "raw", "clickable", "all")),
    ("find", ("REGEX", "index", "clickable", "all")),
    ("tap", ("REGEX", "TIMEOUT", "index", "expect", "interval")),
    ("type", ("REGEX", "TEXT", "clear", "enter", "index")),
    ("wait", ("REGEX", "TIMEOUT", "interval")),
    ("gone", ("REGEX", "TIMEOUT", "interval")),
    ("parse", ("FILE", "match", "clickable", "all")),
)


def build_parser():
    """Return the argument parser; --serial, --literal and -h are handled by split_globals."""
    parser = UsageParser(prog="ui.py", epilog=EPILOG, allow_abbrev=False,
                         description="Label-addressed UI actions on an Android device over adb.",
                         formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)
    for name, keys in LAYOUT:
        command = commands.add_parser(name, allow_abbrev=False)
        for key in keys:
            flag, options = OPTIONS[key]
            command.add_argument(flag, **options)
    return parser


def split_globals(argv):
    """Return (serial, literal, rest), or None when -h or --help comes before the first "--"."""
    serial, literal, rest, arguments = "", False, [], iter(argv)
    for argument in arguments:
        if argument == "--":
            rest.extend(["--", *arguments])
            break
        if argument in ("-h", "--help"):
            return None
        if argument == "--literal":
            literal = True
        elif argument == "--serial":
            serial = require(next(arguments, ""), "Missing value for --serial SERIAL.")
        else:
            rest.append(argument)
    return serial, literal, rest


def main():
    """Run with the process arguments and the documented exit codes."""
    if sys.stdout is None:
        print("Error: cannot write the result: stdout is closed.", file=sys.stderr)
        return EXIT_ERROR
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # dumps are UTF-8
    try:
        parser = build_parser()
        globals_ = split_globals(sys.argv[1:])
        if globals_ is None:
            parser.print_help()
            sys.stdout.flush()
            return EXIT_SUCCESS
        serial, literal, remaining = globals_
        if remaining and remaining[0].startswith("-") and remaining[0] != "--":
            raise Failure(EXIT_ARGUMENT, f'Unknown command: "{remaining[0]}"')
        arguments = parser.parse_args(remaining)
        if arguments.command == "parse":
            code = command_parse(arguments, literal)
        else:
            device = Device(serial)
            if arguments.command == "dump":
                code = command_dump(device, arguments)
            else:
                handlers = {"find": command_find, "tap": command_tap, "type": command_type,
                            "wait": command_wait, "gone": command_gone}
                code = handlers[arguments.command](device, arguments, literal)
        sys.stdout.flush()
        return code
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())  # quiet exit flush
        return EXIT_ERROR
    except Failure as failure:
        print(f"Error: {failure.message}", file=sys.stderr)
        return failure.code


if __name__ == "__main__":
    sys.exit(main())
