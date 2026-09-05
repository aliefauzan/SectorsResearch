import json, re, collections

spec = json.load(open('99-raw/schema.json'))
paths = spec['paths']

GROUPS = [
    ("Indonesia (IDX)", ["Company Screener","Helper Lists","Detailed Reports","Transaction Data",
                          "Rankings","IPO & Performance","News & Filings","Brokers"]),
    ("Singapore (SGX)", ["SGX - Company Screener","SGX - Helper Lists","SGX - Detailed Reports",
                          "SGX - Transaction Data","SGX - Rankings","SGX - News & Filings"]),
    ("Malaysia (KLSE)", ["KLSE"]),
    ("Mining extension (Indonesia)", ["Companies","Commodities & Trade","Production & Sites","Contracts & Licenses"]),
]

def cost_of(desc):
    m = re.search(r'Costs? (1 API credit[^.<\n]*|2 API credits[^.<\n]*|3 API credits[^.<\n]*)', desc or '')
    return m.group(1).strip() if m else "1 API credit (assumed)"

def clean(s, n=160):
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:n] + ("…" if len(s) > n else "")

by_tag = collections.defaultdict(list)
for path, ops in paths.items():
    op = ops.get('get')
    if not op: continue
    tag = (op.get('tags') or ['Untagged'])[0]
    by_tag[tag].append((path, op))

lines = []
W = lines.append
W("# Sectors Financial API — Complete Endpoint Reference (v2)")
W("")
W("> Generated from the official OpenAPI 3.0.3 spec at `https://docs.sectors.app/schema.json`")
W("> (`info.version` = 2.0.0). Raw copy kept at [`99-raw/schema.json`](../99-raw/schema.json).")
W("")
W("**Base URL:** `https://api.sectors.app`")
W("**Auth:** `Authorization: <YOUR_API_KEY>` header (raw key, *no* `Bearer` prefix for the REST API).")
W("")
W("The key comes from the git-ignored `.env` at the repository root — "
  "`from sectors_env import api_key` — never from a literal in code. See "
  "[`SETUP.md`](../../SETUP.md).")
W("")
W("**Method:** every endpoint is `GET`.")
W(f"**Endpoint count:** {sum(len(v) for v in by_tag.values())}")
W("")
W("Legend for the Params column: `name` = optional, **`name`** = required.")
W("")
W("---")
W("")

for group_name, tags in GROUPS:
    W(f"## {group_name}")
    W("")
    for tag in tags:
        items = by_tag.get(tag)
        if not items: continue
        W(f"### {tag}")
        W("")
        W("| Endpoint | What it returns | Credit cost | Params |")
        W("| --- | --- | --- | --- |")
        for path, op in sorted(items):
            params = []
            for p in op.get('parameters', []):
                nm = p.get('name')
                params.append(f"**{nm}**" if p.get('required') else nm)
            W(f"| `{path}` | {clean(op.get('summary') or op.get('description'), 110)} | {cost_of(op.get('description'))} | {', '.join(params) or '—'} |")
        W("")

W("---")
W("")
W("## Per-endpoint detail")
W("")
for group_name, tags in GROUPS:
    for tag in tags:
        for path, op in sorted(by_tag.get(tag, [])):
            W(f"### `GET {path}`")
            W("")
            W(f"**{op.get('summary','')}** — {tag}")
            W("")
            W(clean(op.get('description'), 700))
            W("")
            W(f"- **Credit cost:** {cost_of(op.get('description'))}")
            ps = op.get('parameters', [])
            if ps:
                W("- **Parameters:**")
                W("")
                W("  | Name | In | Type | Required | Description |")
                W("  | --- | --- | --- | --- | --- |")
                for p in ps:
                    sch = p.get('schema', {})
                    typ = sch.get('type', '')
                    if sch.get('enum'):
                        typ += " enum(" + ", ".join(str(e) for e in sch['enum'][:8]) + (", …" if len(sch['enum'])>8 else "") + ")"
                    W(f"  | `{p.get('name')}` | {p.get('in')} | {typ} | {'yes' if p.get('required') else 'no'} | {clean(p.get('description'), 120)} |")
            W("")

open('02-sectors-platform/02-endpoint-reference.md','w').write("\n".join(lines) + "\n")
print("wrote", len(lines), "lines")
