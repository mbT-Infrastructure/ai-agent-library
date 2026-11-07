#!/usr/bin/env python3
"""extract labels, ids and bounds from an adb uiautomator dump.

usage: adb -s <serial> shell cat /sdcard/ui.xml | parse_uidump.py [--clickable | --all]
prints one line per selected node:
"Settings" | desc="" | id="a:b/c" | clickable=true | center=70,150 | bounds=[20,100][120,200]
"""
import argparse
import json
import re
import sys
# The dump is produced by uiautomator on the attached test device, not by an untrusted network
# source, and this skill stays dependency-free, so the stdlib parser is intentional.
import xml.etree.ElementTree as ElementTree  # nosemgrep

BOUNDS_PATTERN = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
MISSING_BOUNDS = '""'


def is_labeled(node):
    """Return True when the node has a text or content-desc label."""
    return bool(node.get("text", "").strip() or node.get("content-desc", "").strip())


def is_unlabeled_clickable(node):
    """Return True for an unlabeled clickable node with a resource-id."""
    return (
        not is_labeled(node)
        and node.get("clickable") == "true"
        and bool(node.get("resource-id", "").strip())
    )


def format_bounds(value):
    """Return (center, bounds) for a bounds attribute."""
    match = BOUNDS_PATTERN.fullmatch(value) if value else None
    if match is None:
        return "-", MISSING_BOUNDS
    x1, y1, x2, y2 = (int(group) for group in match.groups())
    return f"{(x1 + x2) // 2},{(y1 + y2) // 2}", value


def format_node(node):
    """Format one node as a single key=value line."""
    center, bounds = format_bounds(node.get("bounds", ""))
    text = json.dumps(node.get("text", ""), ensure_ascii=False)
    description = json.dumps(node.get("content-desc", ""), ensure_ascii=False)
    resource_id = json.dumps(node.get("resource-id", ""), ensure_ascii=False)
    clickable = node.get("clickable", "")
    return (
        f"{text} | desc={description} | id={resource_id} | clickable={clickable}"
        f" | center={center} | bounds={bounds}"
    )


def main():
    """Parse stdin and print the selected nodes to stdout."""
    # uiautomator dumps are UTF-8; a non-UTF-8 locale must not crash the parser.
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Extract labels, ids and bounds from an adb uiautomator dump."
    )
    parser.add_argument(
        "--clickable",
        action="store_true",
        help="also emit unlabeled clickable nodes that have a resource-id",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="emit every node, including unlabeled ones",
    )
    arguments = parser.parse_args()

    try:
        # Trusted input: the dump comes from the attached device, see the import comment.
        root = ElementTree.fromstring(sys.stdin.read())  # nosemgrep
    except ElementTree.ParseError as error:
        print(f"parse_uidump: invalid XML: {error}", file=sys.stderr)
        return 2

    for node in root.iter("node"):
        selected = (
            arguments.all
            or is_labeled(node)
            or (arguments.clickable and is_unlabeled_clickable(node))
        )
        if selected:
            print(format_node(node))
    return 0


if __name__ == "__main__":
    sys.exit(main())
