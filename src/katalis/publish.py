#!/usr/bin/env python3
"""
D2 `katalis-refresh`: render today's cards and write them to the bucket. Nothing else.

    python3 publish.py --dry-run          render, print what would be written, write nothing
    python3 publish.py --bucket katalis-recorded

**It is not a channel.** It writes objects to Cloud Storage and it has no other exit: no
mail, no webhook, no bot, no push. That is batas eksekusi 1 in `plan/README.md`, and the gate
`check_this_job_is_not_a_channel()` at the bottom enforces it by reading this file's own
source — because the cheapest way for a "daily refresh" to become a daily promise is for
someone to add one line here.

It computes nothing either. Each object's body is the stdout of `card.show()`, the same bytes
`./run.sh pilar` prints and the same bytes `server.py` serves.

Credentials come from the Cloud Run metadata server, so no key file exists and no key is read
from the environment. Run locally with `--dry-run`; a real write outside GCP will fail at the
token step, which is the correct failure.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import pillars as P
import server

METADATA = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
UPLOAD = "https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o"
SCOPE_HOST = "storage.googleapis.com"


def _token():
    request = urllib.request.Request(METADATA, headers={"Metadata-Flavor": "Google"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)["access_token"]


def _put(bucket, name, body, token):
    url = UPLOAD.format(bucket=urllib.parse.quote(bucket, safe="")) + "?" + \
        urllib.parse.urlencode({"uploadType": "media", "name": name})
    request = urllib.request.Request(
        url, data=body.encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "text/plain; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def cards():
    """(object name, body) for every demo case, on the source this job was given."""
    source = os.environ.get("SOURCE", "recorded")
    for case_source, symbol, as_of in P.DEMO_CASES:
        if case_source != source:
            continue
        code, body, err = server.card_text(symbol, as_of, source=case_source)
        if code != 0:
            raise SystemExit(f"{symbol} {as_of}: {err.strip() or 'kartu tidak terbit'}")
        yield f"cards/{source}/{symbol}/{as_of}.txt", body


def run(bucket, dry_run):
    written = 0
    token = None if dry_run else _token()
    for name, body in cards():
        if dry_run:
            print(f"[dry-run] gs://{bucket}/{name}  {len(body.encode('utf-8'))} bytes")
        else:
            _put(bucket, name, body, token)
            print(f"gs://{bucket}/{name}  {len(body.encode('utf-8'))} bytes")
        written += 1
    if not written:
        print(f"SOURCE={os.environ.get('SOURCE', 'recorded')} has no demo case to publish",
              file=sys.stderr)
        return 1
    print(f"{written} kartu {'akan ditulis' if dry_run else 'ditulis'}")
    return 0


# --------------------------------------------------------------------------------- gates

def check_this_job_is_not_a_channel():
    """No transport out of here but the bucket. Read from this file's own source.

    The scan skips the docstrings — which name the forbidden words on purpose — and skips the
    gates themselves, which carry the list. What is left is the code that actually runs when
    Cloud Run starts this job, and that is the only part the rule is about.
    """
    import ast
    failures = []
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    live = [node for node in tree.body
            if not (isinstance(node, ast.FunctionDef)
                    and (node.name.startswith("check_") or node.name == "main"))
            and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
    code = "\n".join(ast.unparse(node) for node in live).lower()
    for forbidden in ("smtplib", "sendmail", "webhook", "slack", "telegram",
                      "twilio", "hooks.", "notify("):
        if forbidden in code:
            failures.append(f"{forbidden!r} appears in this job — it became a channel")
    for node in live:
        for inner in ast.walk(node):
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str) \
                    and inner.value.startswith(("http://", "https://")):
                host = urllib.parse.urlparse(inner.value).hostname or ""
                if host not in (SCOPE_HOST, "metadata.google.internal"):
                    failures.append(f"an outbound URL that is neither GCS nor the metadata "
                                    f"server: {inner.value[:60]}")
    return failures, 10


def check_bodies_are_the_card_verbatim():
    """Each object body must equal what the CLI prints, byte for byte."""
    failures = []
    source = os.environ.get("SOURCE", "recorded")
    cases = [c for c in P.DEMO_CASES if c[0] == source]
    if not cases:
        return [f"no demo case on SOURCE={source}"], 1
    for name, body in cards():
        symbol, as_of = name.split("/")[-2], name.split("/")[-1][:-4]
        _, expected, _ = server.card_text(symbol, as_of, source=source)
        if body != expected:
            failures.append(f"{name}: body is not the card `card.show` printed")
        if "bukan nasihat investasi" not in body.lower():
            failures.append(f"{name}: the no-advice line is missing from the published card")
    return failures, 2 * len(cases)


def check_dry_run_writes_nothing():
    """`--dry-run` must not need a token, so it cannot reach the bucket even by accident."""
    failures = []
    real = globals()["_token"]
    def refuse():
        raise AssertionError("--dry-run asked for a credential")
    globals()["_token"] = refuse
    try:
        if run("katalis-recorded", dry_run=True) != 0:
            failures.append("--dry-run did not succeed on the recorded demo case")
    except AssertionError as exc:
        failures.append(str(exc))
    finally:
        globals()["_token"] = real
    return failures, 1


def main():
    total, bad = 0, []
    for check in (check_this_job_is_not_a_channel, check_bodies_are_the_card_verbatim,
                  check_dry_run_writes_nothing):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<34} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="katalis-refresh", description=__doc__)
    parser.add_argument("--bucket", default=os.environ.get("BUCKET", "katalis-recorded"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true", help="gate ini sendiri")
    args = parser.parse_args()
    raise SystemExit(main() if args.test else run(args.bucket, args.dry_run))
