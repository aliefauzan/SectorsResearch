#!/usr/bin/env python3
"""
Extract every documented example response from the Sectors OpenAPI spec into
one JSON fixture per endpoint.

These fixtures are the *official* shapes Sectors returns, so they are the most
faithful offline stand-in for the live API you can get without burning credits.

Usage:
    python3 src/extract_fixtures.py [--spec ../../evidence/spec/schema.json] [--out ../fixtures]
"""
import argparse
import json
import os
import re


def market_of(path: str) -> str:
    """Which market subdirectory a fixture belongs in.

    70 fixtures in one directory is unreadable, and the endpoint families are already
    disjoint — the path prefix says which market an endpoint serves. Consumers resolve
    fixtures through `_index.json["fixture"]`, which now carries this subdirectory, so
    nothing downstream needs to know the layout.
    """
    p = path.strip("/")
    for prefix in ("sgx", "klse", "mining"):
        if p.startswith(f"v2/{prefix}/"):
            return prefix
    return "idx"


def slugify(path: str) -> str:
    """/v2/company/report/{symbol}/ -> v2_company_report_symbol"""
    s = path.strip("/").replace("{", "").replace("}", "")
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_")


def first_example(operation: dict):
    """Return (example_value, status_code) for the first 2xx JSON example."""
    for status, resp in sorted(operation.get("responses", {}).items()):
        if not str(status).startswith("2"):
            continue
        content = (resp.get("content") or {}).get("application/json") or {}
        if "example" in content:
            return content["example"], status
        examples = content.get("examples") or {}
        for ex in examples.values():
            if "value" in ex:
                return ex["value"], status
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=os.path.join(os.path.dirname(__file__), "..", "..", "evidence", "spec", "schema.json"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "fixtures"))
    args = ap.parse_args()

    spec = json.load(open(args.spec))
    os.makedirs(args.out, exist_ok=True)

    index = {}
    written = skipped = 0

    for path, operations in spec["paths"].items():
        operation = operations.get("get")
        if not operation:
            continue
        example, status = first_example(operation)
        if example is None:
            skipped += 1
            continue

        name = slugify(path)
        rel = os.path.join(market_of(path), name + ".json")
        target = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w") as fh:
            json.dump(example, fh, indent=2, ensure_ascii=False)

        index[path] = {
            "fixture": rel,
            "status": status,
            "summary": operation.get("summary"),
            "tags": operation.get("tags", []),
            "parameters": [
                {
                    "name": p.get("name"),
                    "in": p.get("in"),
                    "required": bool(p.get("required")),
                    "type": (p.get("schema") or {}).get("type"),
                    # Multi-select parameters (`sections`, `classifications`, `periods`)
                    # are `type: array` and carry their enum on `items`, not on the
                    # schema itself. Reading only `schema.enum` dropped all 12 of them
                    # -- which are exactly the parameters that drive billing -- so the
                    # mock could not reject an out-of-enum section and billed the typo
                    # instead.
                    "enum": ((p.get("schema") or {}).get("enum")
                             or ((p.get("schema") or {}).get("items") or {}).get("enum")),
                    "minimum": (p.get("schema") or {}).get("minimum"),
                    "maximum": (p.get("schema") or {}).get("maximum"),
                }
                for p in operation.get("parameters", [])
            ],
            "credit_cost": credit_cost(operation.get("description", "")),
            "credit_default_items": credit_default_items(operation.get("description", "")),
        }
        written += 1

    with open(os.path.join(args.out, "_index.json"), "w") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)

    print(f"wrote {written} fixtures, skipped {skipped} endpoints without examples")
    print(f"index -> {os.path.join(args.out, '_index.json')}")


def credit_cost(description: str) -> str:
    match = re.search(r"Costs? (1 API credit[^.<\n]*|2 API credits[^.<\n]*|3 API credits[^.<\n]*)", description or "")
    return match.group(1).strip() if match else "1 API credit (assumed)"


def credit_default_items(description: str):
    """How many items a per-item endpoint bills when the parameter is omitted.

    The spec states this as e.g. "Default behavior (all 6 sections) consumes 6
    credits". It differs per endpoint - 8 sections for the IDX company report,
    6 for the subsector report, 4 for SGX/KLSE - so the mock cannot assume one
    number for the whole family.
    """
    match = re.search(r"Default behavior \((?:all )?(\d+)(?: classifications?)?", description or "")
    return int(match.group(1)) if match else None


if __name__ == "__main__":
    main()
