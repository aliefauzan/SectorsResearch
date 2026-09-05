#!/usr/bin/env python3
"""Generate the response data dictionary from the extracted OpenAPI fixtures."""
import json
import os

FIXTURES = "03-mock-data/fixtures"
OUT = "02-sectors-platform/07-response-shapes.md"

GROUPS = [
    ("Indonesia (IDX)", ["Company Screener", "Helper Lists", "Detailed Reports",
                         "Transaction Data", "Rankings", "IPO & Performance",
                         "News & Filings", "Brokers"]),
    ("Singapore (SGX)", ["SGX - Company Screener", "SGX - Helper Lists",
                         "SGX - Detailed Reports", "SGX - Transaction Data",
                         "SGX - Rankings", "SGX - News & Filings"]),
    ("Malaysia (KLSE)", ["KLSE"]),
    ("Mining extension", ["Companies", "Commodities & Trade",
                          "Production & Sites", "Contracts & Licenses"]),
]


def envelope(value):
    """One-line description of the outermost container."""
    if isinstance(value, list):
        return "bare array"
    if isinstance(value, dict):
        if "results" in value and "pagination" in value:
            return "`{results, pagination}` envelope"
        return "object"
    return type(value).__name__


def keys_of(value, limit=18):
    if isinstance(value, dict):
        keys = list(value.keys())
        shown = ", ".join(f"`{k}`" for k in keys[:limit])
        return shown + (f" … (+{len(keys) - limit})" if len(keys) > limit else "")
    if isinstance(value, list) and value and isinstance(value[0], dict):
        keys = list(value[0].keys())
        shown = ", ".join(f"`{k}`" for k in keys[:limit])
        return shown + (f" … (+{len(keys) - limit})" if len(keys) > limit else "")
    if isinstance(value, list) and value:
        return f"array of `{type(value[0]).__name__}`"
    return "—"


def row_keys(value, limit=18):
    """Keys of the repeating row, when the payload wraps a list."""
    if isinstance(value, dict):
        for candidate in ("results", "data"):
            inner = value.get(candidate)
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                return candidate, keys_of(inner, limit)
        for key, inner in value.items():
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                return key, keys_of(inner, limit)
    return None, None


def main():
    index = json.load(open(os.path.join(FIXTURES, "_index.json")))
    by_tag = {}
    for path, meta in index.items():
        tag = (meta.get("tags") or ["Untagged"])[0]
        by_tag.setdefault(tag, []).append((path, meta))

    lines = []
    W = lines.append
    W("# Response Shapes — What Each Endpoint Actually Returns")
    W("")
    W("> Generated from the official example response attached to every endpoint in the")
    W("> OpenAPI spec. Full payloads are in [`../03-mock-data/fixtures/`](../03-mock-data/fixtures/)")
    W("> — one JSON file per endpoint, named after the path.")
    W("")
    W("The API is not uniform: some endpoints return a bare array, some a `{results, pagination}`")
    W("envelope, some a bespoke object with named sub-lists. **Check this page before writing a")
    W("parser** — assuming the wrong container is the most common integration bug against this API.")
    W("")
    W("Legend: **Envelope** is the outermost container. **Row keys** are the fields on the")
    W("repeating record inside, where there is one.")
    W("")
    W("---")
    W("")
    for group, tags in GROUPS:
        W(f"## {group}")
        W("")
        for tag in tags:
            items = by_tag.get(tag)
            if not items:
                continue
            W(f"### {tag}")
            W("")
            for path, meta in sorted(items):
                payload = json.load(open(os.path.join(FIXTURES, meta["fixture"])))
                W(f"**`{path}`** — {meta.get('summary','')}")
                W("")
                W(f"- Envelope: {envelope(payload)}")
                if isinstance(payload, dict):
                    W(f"- Top-level keys: {keys_of(payload)}")
                name, keys = row_keys(payload)
                if name:
                    W(f"- Row keys (inside `{name}`): {keys}")
                elif isinstance(payload, list):
                    W(f"- Row keys: {keys_of(payload)}")
                W(f"- Fixture: [`{meta['fixture']}`](../03-mock-data/fixtures/{meta['fixture']})")
                W("")
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("wrote", OUT, len(lines), "lines")


if __name__ == "__main__":
    main()
