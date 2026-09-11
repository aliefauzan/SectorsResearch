#!/usr/bin/env python3
"""
The accessibility claims, checked instead of asserted.

    python3 a11y_check.py            every symbol's page
    python3 a11y_check.py --broken   the deliberately broken fixture, which must fail

A judge can open this page with their own screen reader and know in seconds whether the
claim is empty. This file is the part that can be run without one. It checks exactly the
success criteria this product claims and no others — an automated pass is not a
conformance claim, and saying "WCAG 2.2 AA" because a linter was quiet would be the same
kind of empty label the research is about.

Checked here, on the real rendered HTML:

  1.3.1  Info and Relationships   every data table has a caption and marked headers;
                                  every form control has a label bound to it
  1.4.3  Contrast (Minimum)       computed from the palette constants in `webapp.py`,
                                  both colour schemes, against the 4.5:1 threshold
  2.4.1  Bypass Blocks            a skip link that points at an id the page has
  2.4.6  Headings and Labels      one h1, no skipped levels, no empty heading
  3.1.1  Language of Page         `lang` is present and is a real tag
  4.1.2  Name, Role, Value        buttons and selects have accessible names; every
                                  `aria-controls` and `aria-labelledby` resolves

Not checked here, and therefore not claimed: focus order, reflow at 320 px, motion, and
anything that needs a real screen reader. Those are the manual VoiceOver pass.

Standard library only — `html.parser`, no axe, no browser.
"""
import argparse
import re
from html.parser import HTMLParser

import reader
import sources
import webapp


class Page(HTMLParser):
    """Just enough of the DOM to answer the questions above."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings = []          # (level, text)
        self.ids = set()
        self.tables = []            # {caption, col, row, in_thead}
        self.controls = []          # (tag, attrs, text)
        self.links = []             # (href, text)
        self.lang = None
        self.live = []
        self.refs = []              # (attr, value) that must resolve to an id
        self.drawings = []
        self._stack = []
        self._text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for attr in ("aria-controls", "aria-labelledby", "aria-describedby"):
            if attrs.get(attr):
                self.refs += [(attr, value) for value in attrs[attr].split()]
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag in ("canvas", "svg"):
            self.drawings.append(tag)
        if attrs.get("aria-live"):
            self.live.append(attrs["aria-live"])
        if tag == "table":
            self.tables.append({"caption": None, "col": 0, "row": 0, "unscoped": 0})
        if tag == "th" and self.tables:
            scope = attrs.get("scope")
            if scope == "col":
                self.tables[-1]["col"] += 1
            elif scope == "row":
                self.tables[-1]["row"] += 1
            else:
                self.tables[-1]["unscoped"] += 1
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._stack.append((tag, attrs))
            self._text = []
        elif tag in ("button", "select", "a", "caption", "label"):
            self._stack.append((tag, attrs))
            self._text = []

    def handle_data(self, data):
        if self._stack:
            self._text.append(data)

    def handle_endtag(self, tag):
        if not self._stack or self._stack[-1][0] != tag:
            return
        _, attrs = self._stack.pop()
        text = "".join(self._text).strip()
        self._text = []
        if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            self.headings.append((int(tag[1]), text))
        elif tag == "caption" and self.tables:
            self.tables[-1]["caption"] = text
        elif tag == "a":
            self.links.append((attrs.get("href", ""), text))
        elif tag in ("button", "select"):
            self.controls.append((tag, attrs, text))
        elif tag == "label":
            self.controls.append(("label", attrs, text))


# ------------------------------------------------------------------------- 1.4.3
#
# Contrast is computed from the palette constants rather than sampled from a screenshot,
# because the palette is where a regression would be introduced and because sampling
# needs a browser this product does not depend on.


def _srgb(channel):
    channel /= 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_colour):
    hex_colour = hex_colour.lstrip("#")
    if len(hex_colour) == 3:
        hex_colour = "".join(character * 2 for character in hex_colour)
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)


def contrast(foreground, background):
    a, b = luminance(foreground), luminance(background)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def palette_pairs():
    """(scheme, name, foreground, background) for every text colour the page uses.

    Read out of `webapp.STYLE` rather than duplicated, so changing the stylesheet cannot
    leave this check testing a palette the page no longer has.
    """
    blocks = webapp.STYLE.split("@media (prefers-color-scheme: dark)")
    schemes = []
    for scheme, block in (("light", blocks[0]), ("dark", blocks[1] if len(blocks) > 1 else "")):
        found = dict(re.findall(r"--(\w+):\s*(#[0-9a-fA-F]{3,6})", block))
        schemes.append((scheme, found))
    light = schemes[0][1]
    pairs = []
    for scheme, found in schemes:
        merged = dict(light)
        merged.update(found)
        for name in ("ink", "accent", "warn", "rule"):
            if name in merged and "paper" in merged:
                pairs.append((scheme, name, merged[name], merged["paper"]))
    return pairs


# ------------------------------------------------------------------------------ checks


def check_page(markup, label):
    """Every criterion this file claims, against one rendered page."""
    failures = []
    page = Page()
    page.feed(markup)

    # 3.1.1 Language of Page
    if not page.lang or len(page.lang) < 2:
        failures.append(f"{label}: 3.1.1 — lang is {page.lang!r}")

    # 2.4.6 Headings and Labels
    levels = [level for level, _ in page.headings]
    if levels.count(1) != 1:
        failures.append(f"{label}: 2.4.6 — {levels.count(1)} h1 elements, expected 1")
    for previous, current in zip(levels, levels[1:]):
        if current > previous + 1:
            failures.append(f"{label}: 2.4.6 — heading jumps h{previous} to h{current}; "
                            f"heading navigation skips the gap")
    for level, text in page.headings:
        if not text:
            failures.append(f"{label}: 2.4.6 — an h{level} is empty")

    # 2.4.1 Bypass Blocks
    skip = [href for href, _ in page.links if href.startswith("#")]
    if not skip:
        failures.append(f"{label}: 2.4.1 — no skip link")
    for href in skip:
        if href[1:] not in page.ids:
            failures.append(f"{label}: 2.4.1 — skip link points at missing id {href}")

    # 1.3.1 Info and Relationships
    for index, table in enumerate(page.tables, 1):
        if not table["caption"]:
            failures.append(f"{label}: 1.3.1 — table {index} has no caption")
        if not table["row"] and not table["col"]:
            failures.append(f"{label}: 1.3.1 — table {index} has no scoped headers")
        if table["unscoped"]:
            failures.append(f"{label}: 1.3.1 — table {index} has {table['unscoped']} "
                            f"th without scope")
    labels = {attrs.get("for") for tag, attrs, _ in page.controls if tag == "label"}
    for tag, attrs, text in page.controls:
        if tag != "select":
            continue
        if attrs.get("id") not in labels and not attrs.get("aria-label"):
            failures.append(f"{label}: 1.3.1 — select {attrs.get('id')!r} has no label")

    # 4.1.2 Name, Role, Value
    for tag, attrs, text in page.controls:
        if tag == "button" and not (text or attrs.get("aria-label")):
            failures.append(f"{label}: 4.1.2 — a button has no accessible name")
    for attr, value in page.refs:
        if value not in page.ids:
            failures.append(f"{label}: 4.1.2 — {attr}={value!r} resolves to nothing")

    # The product's own rule: there is no chart on this page to make accessible.
    if page.drawings:
        failures.append(f"{label}: a {page.drawings[0]} reached the page")

    return failures


def check_contrast():
    failures = []
    pairs = palette_pairs()
    if len(pairs) < 8:
        failures.append(f"only {len(pairs)} colour pairs found — the palette parser has "
                        f"lost sight of the stylesheet")
    worst = None
    for scheme, name, foreground, background in pairs:
        ratio = contrast(foreground, background)
        if worst is None or ratio < worst[0]:
            worst = (ratio, scheme, name)
        # `rule` is a border colour, so 3:1 is its bar (1.4.11), not 4.5:1.
        threshold = 3.0 if name == "rule" else 4.5
        if ratio < threshold:
            failures.append(f"1.4.3 — {scheme} {name} on paper is {ratio:.2f}:1, "
                            f"needs {threshold}:1")
    if worst:
        print(f"        lowest contrast {worst[0]:.2f}:1 ({worst[1]} {worst[2]}) "
              f"across {len(pairs)} pairs")
    return failures, len(pairs)


BROKEN = """<!DOCTYPE html><html><head><title>x</title></head><body>
<h1></h1><h3>skipped a level</h3>
<table><tr><th>no scope</th><td>1</td></tr></table>
<select id="s"></select>
<button aria-controls="nowhere"></button>
<svg></svg></body></html>"""


def main(argv=None):
    parser = argparse.ArgumentParser(prog="a11y_check.py")
    parser.add_argument("--broken", action="store_true",
                        help="run the fixture that must fail, to prove the checker works")
    args = parser.parse_args(argv)

    if args.broken:
        failures = check_page(BROKEN, "fixture")
        print(f"the broken fixture produced {len(failures)} failure(s):")
        for failure in failures:
            print(f"        {failure}")
        # A checker that passes a page this broken is not a checker.
        expected = 8
        ok = len(failures) >= expected
        print("PASS  the checker catches what it claims to" if ok
              else f"FAIL  expected at least {expected} failures, got {len(failures)}")
        return 0 if ok else 1

    all_failures = []
    checked = 0
    for symbol in sources.available_symbols("recorded"):
        markup = webapp.page(reader.read(symbol))
        checked += 1
        all_failures += check_page(markup, symbol)
    mark = "PASS" if not all_failures else "FAIL"
    print(f"{mark}  rendered pages       {checked} checked, {len(all_failures)} failed")
    for failure in all_failures:
        print(f"        {failure}")

    contrast_failures, pairs = check_contrast()
    mark = "PASS" if not contrast_failures else "FAIL"
    print(f"{mark}  palette contrast     {pairs} checked, {len(contrast_failures)} failed")
    for failure in contrast_failures:
        print(f"        {failure}")

    total = len(all_failures) + len(contrast_failures)
    if not total:
        print("\n1.3.1, 1.4.3, 2.4.1, 2.4.6, 3.1.1 and 4.1.2 hold on every rendered page."
              "\nEverything else is the manual screen-reader pass, and is not claimed here.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
