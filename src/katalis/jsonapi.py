#!/usr/bin/env python3
"""
The read-only JSON surface: the figures the card already prints, as data.

    GET /json/card/{symbol}?date=YYYY-MM-DD    the tape, the broker evidence, the four pillars
    GET /json/symbols                          what this source can actually serve

Why this is a sibling of `server.py` and not a few more lines inside it: `server.py`'s own
gate `check_this_module_computes_nothing` scans that module's product code and fails on the
first `sources.`, `thresholds.`, `P.assess(` or `P.bag_from(` above its gates — and this
surface exists precisely to call those readers. Splitting the projection out is what lets
both gates stay green instead of one of them being loosened to make room. The routing still
lives in `server.py`; only the projection lives here.

**It computes nothing, and three gates say so rather than this paragraph:**

  1. `check_no_arithmetic_in_this_module` parses this file and fails on the first `BinOp` or
     `AugAssign` above the gates. There is no `+`, no `*`, no `sum()`, no mean and no z-score
     anywhere in the code that runs — every number is a value another module already
     produced, carried across unchanged.
  2. `check_metrics_are_the_existing_figures` holds every metric in the reply against the
     `Figure` `pillars.assess()` built, field by field. A number invented here has nowhere to
     come from, and the gate goes red.
  3. `check_imports_are_readers_only` limits the imports to the readers in `sources.py`, the
     figures in `pillars.py`, the renderer in `card.py` and the table in `thresholds.py`.
     `math`, `statistics`, `random`, `datetime` and their friends are refused, because
     importing one of them is how a projection starts becoming an engine.

A field the UI wants that no module in this product produces is **not invented here**. It is
named in `UNAVAILABLE` with the reason, the reply carries `null` in its place and the whole
list under `unavailable`. `plan/inputs/ui-data-contract.md` is the contract that documents
every path, its unit and where its number comes from.

No socket is opened outward, no key is read, and the only files touched are the two local
data layers. That is batas eksekusi 2 in `plan/README.md`: the deploy exposes what exists.
"""
import json
import os

import card
import classify
import pillars as P
import sources
import thresholds as T

JSON_CT = "application/json; charset=utf-8"

#: The reason each unavailable field is unavailable, and a dotted `path` into the reply so the
#: gate can prove the list is telling the truth. `[]` walks every element of a list.
UNAVAILABLE = (
    {"path": "broker.buyers",
     "reason": "Net per broker across the window is computed inside "
               "pillars.concentration() and never returned by it. Rebuilding that sum here "
               "would be new market arithmetic on the surface; broker.rows carries the "
               "per-day payload verbatim instead."},
    {"path": "broker.sellers",
     "reason": "Same as broker.buyers: the seller side is not produced by any function this "
               "product exposes."},
    {"path": "broker.netForeign",
     "reason": "A single foreign-flow total over the window is not produced anywhere. "
               "broker.foreignFlow carries the per-date net_foreign_inflow rows verbatim, "
               "and it is null on a source that never recorded /v2/foreign-flow/."},
    {"path": "broker.totalMarketValue",
     "reason": "Gross traded value across the window is not computed by any module here."},
    {"path": "broker.freeFloatShares",
     "reason": "free_float x shares_outstanding is arithmetic pillars.concentration() does "
               "internally and does not expose. Both inputs are served verbatim under "
               "free_float and shares_outstanding, with their own citations."},
    {"path": "broker.referencePrice",
     "reason": "No payload on either data layer carries an IDX reference price, and nothing "
               "in the product derives one."},
    {"path": "pillars[].calculation",
     "reason": "The pillars emit a headline and cited figures, never a formula/substitution "
               "pair. The nearest honest thing is the figure's own note, served under "
               "pillars[].metrics[].note."},
)


def _reply(status, document):
    return status, JSON_CT, json.dumps(document, sort_keys=True, ensure_ascii=False, indent=2)


def bad_request(message):
    """A JSON refusal, so a caller that speaks JSON is answered in JSON."""
    return _reply(400, {"ok": False, "error": message})


def not_found(message):
    return _reply(404, {"ok": False, "error": message})


def _die(status, message):
    return _reply(status, {"ok": False, "error": message})


def _index_closes(source):
    """ISO date -> IHSG close, straight out of `sources.index_daily`. Empty when absent."""
    try:
        return {row["date"]: row["close"] for row in sources.index_daily(source)}
    except (sources.NotRecorded, ValueError):
        return {}


def _price_series(source, symbol, as_of):
    """The last `baseline_days` trading days ending at `as_of`, index joined by date.

    The window is the one `pillars.window_dates()` picks — the same 45 trading days the
    momentum baseline is taken over — so the chart the UI draws and the baseline the product
    reasons from are the same rows. `close` and `volume` are `sources.daily`'s own values;
    `ihsg` is `sources.index_daily`'s close on the same date, or null when the index has no
    row that day.
    """
    daily = sources.daily(source, symbol)
    closes = _index_closes(source)
    by_date = {row["date"]: row for row in daily}
    return [{"date": day, "close": by_date[day]["close"], "ihsg": closes.get(day),
             "volume": by_date[day]["volume"]}
            for day in P.window_dates(daily, as_of, T.get("baseline_days"))]


def _foreign_flow(source, symbol, as_of):
    """Per-date `net_foreign_inflow` up to `as_of`, or None when the source has no tape."""
    try:
        return P.upto(sources.foreign_flow(source, symbol), as_of)
    except (sources.NotRecorded, ValueError):
        return None


def _broker(source, symbol, as_of, result, bag):
    """Broker evidence for the event window, and the fields no module produces.

    `rows` is `sources.broker_flow`'s own normalized output, filtered to the window the
    concentration pillar measured, plus the registry join `pillars.concentration()` uses for
    origin and cohort. The wrapped values — the buyer and seller lists, the foreign total,
    the market value, the free-float share count, the reference price — are null, and each
    one's reason is in `unavailable`.
    """
    window = set(result["window"])
    registry = bag.get("registry") or {}
    rows = []
    for row in bag.get("flow") or []:
        if row["date"] not in window:
            continue
        meta = registry.get(row["broker_code"]) or {}
        rows.append({"date": row["date"], "code": row["broker_code"],
                     "net_idr": row["net_idr"], "buy_idr": row["buy_idr"],
                     "sell_idr": row["sell_idr"], "net_lot": row["net_lot"],
                     "avg_buy_price": row["avg_buy_price"],
                     "origin_inline": row["origin_inline"],
                     "cohort_inline": row["cohort_inline"],
                     "name": meta.get("name"), "is_foreign": meta.get("is_foreign"),
                     "cohort": meta.get("cohort")})
    return {"window": list(result["window"]), "rows": rows,
            "foreignFlow": _foreign_flow(source, symbol, as_of),
            "buyers": None, "sellers": None, "netForeign": None, "totalMarketValue": None,
            "freeFloatShares": None, "referencePrice": None}


def _metric(figure):
    return {"name": figure.name, "value": figure.value, "unit": figure.unit,
            "note": figure.note, "endpoint": figure.endpoint, "fields": list(figure.fields)}


def _pillars(result):
    return [{"name": pillar.name, "status": pillar.status, "headline": pillar.headline,
             "metrics": [_metric(figure) for figure in pillar.figures],
             "unchecked": list(pillar.unchecked), "calculation": None}
            for pillar in result["pillars"]]


def _free_float(source, symbol):
    try:
        return sources.free_float(source, symbol)
    except (sources.NotRecorded, ValueError):
        return None


def _shares(source, symbol):
    try:
        value, fields, exact = sources.shares_outstanding(source, symbol)
    except (sources.NotRecorded, ValueError):
        return {"value": None, "fields": [], "exact": False}
    return {"value": value, "fields": list(fields), "exact": exact}


def document(source, symbol, as_of, result):
    """The whole reply, assembled from values other modules already produced."""
    bag = P.bag_from(source, symbol, as_of)
    return {
        "ok": True,
        "source": source,
        "symbol": result["symbol"],
        "name": sources.company_name(source, symbol),
        "profile": sources.company_profile(source, symbol),
        "as_of": result["as_of"],
        "classifier": result["classifier"],
        "decision": {"verdict": result["verdict"],
                     "modifiers": list(result["modifiers"]),
                     "window": list(result["window"])},
        "price_series": _price_series(source, symbol, as_of),
        "broker": _broker(source, symbol, as_of, result, bag),
        "free_float": _free_float(source, symbol),
        "shares_outstanding": _shares(source, symbol),
        "pillars": _pillars(result),
        "modifier_metrics": [_metric(figure)
                             for figure in result.get("modifier_figures") or []],
        "thresholds": list(result["thresholds"]),
        "unavailable": [dict(entry) for entry in UNAVAILABLE],
    }


def card_response(symbol, as_of, source):
    """`(status, content_type, body)` for one JSON card. The statuses mirror the text route."""
    try:
        rows = sources.daily(source, symbol)
    except (sources.NotRecorded, ValueError):
        return not_found(f"{symbol}: tidak ada deret harga di sumber {source}")
    if not rows:
        return not_found(f"{symbol}: tidak ada deret harga di sumber {source}")
    as_of = as_of or rows[-1]["date"]
    classifier = card.selected_classifier()
    try:
        bag = P.bag_from(source, symbol, as_of)
        result = P.assess(bag, symbol, as_of, classifier=classifier)
    except P.Rejected as exc:
        return not_found(f"{sources.bare(symbol)} {as_of}: TIDAK DINILAI — {exc}")
    except classify.UnknownClassifier as exc:
        # A misconfigured revision says so, the same way the text route does.
        return _die(500, str(exc))
    return _reply(200, document(source, symbol, as_of, result))


def _broker_dates(source, symbol):
    """The dates the broker tape covers for this symbol. Not a promise that a card exists.

    Without a broker summary the concentration pillar has nothing to read and `assess()`
    refuses the whole card, so on a source where only two symbols were ever captured with
    broker rows, asking for "the latest date" gets a refusal for everyone else. These are the
    only dates worth asking about, read off the payload on disk at no cost.

    It is deliberately *not* a list of assessable dates. Whether a date is assessable depends
    on preconditions `pillars.assess()` owns — the baseline has to be long enough, for one —
    and re-deciding that here would be a second copy of a rule that already exists, free to
    drift from the one that runs. A caller walks these newest first and reads the refusal.
    """
    try:
        rows = sources.broker_flow(source, symbol)
    except (sources.NotRecorded, ValueError):
        return []
    return sorted({row["date"] for row in rows})


def symbols_response(source):
    """What this source can serve, and the window each symbol actually holds."""
    rows = []
    for symbol in sources.available_symbols(source):
        daily = sources.daily(source, symbol)
        rows.append({"symbol": symbol, "name": sources.company_name(source, symbol),
                     "profile": sources.company_profile(source, symbol),
                     "days": len(daily),
                     "first": daily[0]["date"] if daily else None,
                     "last": daily[-1]["date"] if daily else None,
                     "last_close": daily[-1]["close"] if daily else None,
                     "last_volume": daily[-1]["volume"] if daily else None,
                     "broker_dates": _broker_dates(source, symbol)})
    return _reply(200, {"ok": True, "source": source, "symbols": rows})


# --------------------------------------------------------------------------------- gates

#: Import names the projection is allowed to reach for. Everything on this list is a reader
#: (`sources`), a table (`thresholds`), a renderer (`card`) or the figures themselves
#: (`pillars`). Adding a name here to make room for arithmetic is the change this gate exists
#: to make visible in a diff.
READERS = ("json", "os", "card", "classify", "pillars", "sources", "thresholds")

#: Names that would mean this file had grown its own math. Each one is a function that exists
#: in a module this file may call; none of them may be reimplemented here.
COMPUTE = ("robust_z", "ols_beta", "log_returns", "median", "statistics", "math.",
          "random.", "datetime", "expm1", "hhi")


def _product_code():
    """This file's product code — above the gates marker — as parsed nodes and as code text.

    The text is `ast.unparse` of the tree with every docstring dropped, not the raw source.
    The token scan below looks for the *name* of a calculator, and the paragraph at the top of
    this file names the modules it refuses; scanning raw bytes made the prose that documents
    the rule fail the rule. Comments disappear with `unparse`, docstrings are removed by hand,
    and what is left is only what runs — which is the only thing the scan was ever about.
    """
    import ast
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text.split("--------- gates", 1)[0])
    holders = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        if not isinstance(node, holders):
            continue
        head = node.body[0] if node.body else None
        if (isinstance(head, ast.Expr) and isinstance(head.value, ast.Constant)
                and isinstance(head.value.value, str)):
            node.body = node.body[1:] or [ast.Pass()]
    return tree, ast.unparse(tree)


def check_no_arithmetic_in_this_module():
    """The projection may not compute. No binary operator, no augmented assignment, ever.

    Reading the operator nodes rather than grepping for characters is what makes this
    checkable: a `+` inside a URL string is not an operator, and the gate would be useless if
    it could not tell the difference. Any `BinOp` above the gates is a number being made here
    rather than carried across, and it fails.
    """
    import ast
    failures = []
    tree, _text = _product_code()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            failures.append(f"line {node.lineno}: an operator builds a value on the surface")
        elif isinstance(node, ast.AugAssign):
            failures.append(f"line {node.lineno}: an augmented assignment mutates a value")
        elif isinstance(node, ast.Lambda):
            failures.append(f"line {node.lineno}: a lambda hides a computation")
    return failures, 3


def check_imports_are_readers_only():
    """Only readers, the figure producer, the renderer and the table may be imported.

    Plus the token scan: an import is one way to get a calculator in here, and calling a
    pillar's internal helper by a fully qualified name is the other.
    """
    import ast
    failures = []
    tree, text = _product_code()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        for name in names:
            if name.split(".")[0] not in READERS:
                failures.append(f"line {node.lineno}: this file imports {name!r}, "
                                f"which is not a reader")
    for needle in COMPUTE:
        if needle in text:
            failures.append(f"{needle!r} appears above the gates — this file grew math")
    return failures, 2 + len(COMPUTE)


def _cases():
    """The demo cases on the source this process serves. The surface exposes one SOURCE."""
    import server
    return [case for case in P.DEMO_CASES if case[0] == server.SOURCE]


def _fetch(path):
    import urllib.error
    import urllib.request
    import server
    httpd, port = server._running()
    try:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=30) as reply:
                return reply.status, reply.headers.get("Content-Type"), reply.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type"), exc.read().decode("utf-8")
    finally:
        httpd.shutdown()


def check_response_shape():
    """Both endpoints answer over a real socket, and the card reply has the agreed shape."""
    failures = []
    cases = _cases()
    if not cases:
        return [f"no demo case runs on SOURCE; the JSON surface is untested"], 1
    _source, symbol, as_of = cases[0]
    status, ctype, body = _fetch(f"/json/card/{symbol}?date={as_of}")
    if status != 200:
        return [f"/json/card/{symbol} returned {status}"], 1
    if not (ctype or "").startswith("application/json"):
        failures.append(f"/json/card answered Content-Type {ctype!r}")
    try:
        doc = json.loads(body)
    except ValueError as exc:
        return failures + [f"the reply is not JSON: {exc}"], 1
    if doc.get("ok") is not True:
        failures.append("ok is not true on a served card")
    if doc.get("symbol") != sources.bare(symbol) or doc.get("as_of") != as_of:
        failures.append(f"the reply names {doc.get('symbol')} {doc.get('as_of')}")
    series = doc.get("price_series") or []
    if not series:
        failures.append("price_series is empty")
    else:
        keys = sorted(series[0])
        if keys != ["close", "date", "ihsg", "volume"]:
            failures.append(f"a price row carries {keys}")
        dates = [row["date"] for row in series]
        if dates != sorted(dates):
            failures.append("price_series is not ascending")
        if max(dates) > as_of:
            failures.append("price_series reaches past as_of")
        if len(series) != len(P.window_dates(sources.daily(_source, symbol), as_of,
                                             T.get("baseline_days"))):
            failures.append("price_series is not the baseline window")
    broker = doc.get("broker") or {}
    if not broker.get("rows"):
        failures.append("broker.rows is empty")
    elif not all("is_foreign" in row and "net_idr" in row for row in broker["rows"]):
        failures.append("a broker row lost its registry join or its net")
    pillars = doc.get("pillars") or []
    if [p.get("name") for p in pillars] != ["konsentrasi", "volume", "momentum", "katalis"]:
        failures.append(f"pillars are {[p.get('name') for p in pillars]}")
    for pillar in pillars:
        if not pillar.get("headline") or not pillar.get("metrics"):
            failures.append(f"{pillar.get('name')}: no headline or no metrics")
        for metric in pillar.get("metrics") or []:
            if not metric.get("endpoint") or not metric.get("fields"):
                failures.append(f"{pillar.get('name')}.{metric.get('name')}: uncited metric")
    if not doc.get("thresholds"):
        failures.append("no threshold provenance was served")
    for entry in doc.get("thresholds") or []:
        if entry.get("origin") not in ("shipped", "learned"):
            failures.append(f"{entry.get('name')}: origin {entry.get('origin')!r}")
    if not (doc.get("decision") or {}).get("verdict"):
        failures.append("the reply carries no verdict")
    listing_status, _ctype, listing = _fetch("/json/symbols")
    if listing_status != 200:
        failures.append(f"/json/symbols returned {listing_status}")
    else:
        listed = json.loads(listing).get("symbols") or []
        served = [row["symbol"] for row in listed]
        if sources.bare(symbol) not in served:
            failures.append(f"{symbol} is absent from /json/symbols")
        columns = sorted(listed[0]) if listed else []
        if columns != ["broker_dates", "days", "first", "last", "last_close", "last_volume",
                       "name", "profile", "symbol"]:
            failures.append(f"a listing row carries {columns}")
    return failures, 14


def check_profile_is_the_narrowed_overview():
    """The served profile is `sources.PROFILE_FIELDS` exactly — no wider, no invented key.

    The company report is a large payload with an address, a phone number and an email in it.
    Narrowing happens in `sources.company_profile`, and this gate is what keeps the narrowing
    from quietly widening later: a surface that served the whole `overview` would be shipping
    contact details it never needed, and nobody would notice from the card.
    """
    failures = []
    checked = 0
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        served = document(source, symbol, as_of, result)["profile"]
        checked += 1
        if served is None:
            continue
        if sorted(served) != sorted(sources.PROFILE_FIELDS):
            failures.append(f"{symbol}: the profile carries {sorted(served)}")
    return failures, checked


def check_broker_dates_answer_with_a_reason():
    """Every advertised date answers 200, or 404 with a refusal that names its cause.

    The listing says where the broker tape is; it does not say a card exists there. What it
    may never do is point at a date the route cannot explain. On this source one symbol has
    broker rows whose baseline is too short to assess, and the value of this gate is that the
    reader gets `baseline_tipis: 4 hari baseline` instead of a bare 404 — the absence is
    described, which is the same rule the card follows everywhere else.
    """
    failures = []
    checked = 0
    status, _ctype, listing = _fetch("/json/symbols")
    if status != 200:
        return [f"/json/symbols returned {status}"], 1
    for row in json.loads(listing).get("symbols") or []:
        for date in (row.get("broker_dates") or [])[-2:]:
            checked += 1
            served, _ctype, body = _fetch(f"/json/card/{row['symbol']}?date={date}")
            if served == 200:
                continue
            if served != 404:
                failures.append(f"{row['symbol']} {date} answered {served}")
            elif "TIDAK DINILAI" not in json.loads(body).get("error", ""):
                failures.append(f"{row['symbol']} {date} was refused without a reason")
    return failures, checked or 1


def check_determinism():
    """The same request twice must be the same bytes. A dict iteration order must not leak."""
    failures = []
    cases = _cases()
    if not cases:
        return ["no demo case to repeat"], 1
    _source, symbol, as_of = cases[0]
    path = f"/json/card/{symbol}?date={as_of}"
    first = _fetch(path)[2]
    second = _fetch(path)[2]
    if first != second:
        failures.append("two identical /json/card requests returned different bytes")
    one = _fetch("/json/symbols")[2]
    two = _fetch("/json/symbols")[2]
    if one != two:
        failures.append("two identical /json/symbols requests returned different bytes")
    # Sorted keys and a fixed indent are why the bytes above are stable; a reply that lost
    # them would still be valid JSON and would still parse, so it is asserted, not assumed.
    resorted = json.dumps(json.loads(first), sort_keys=True, ensure_ascii=False, indent=2)
    if resorted != first:
        failures.append("the reply is not emitted with sorted keys and a fixed indent")
    return failures, 3


def check_no_secret_in_json():
    """A key in the environment must not appear in any JSON body, on any route or refusal."""
    failures = []
    sentinel = "KATALIS-SENTINEL-json-4a91"
    before = os.environ.get("SECTORS_API_KEY")
    os.environ["SECTORS_API_KEY"] = sentinel
    cases = _cases()
    if not cases:
        return ["no demo case to probe"], 1
    _source, symbol, as_of = cases[0]
    probes = [f"/json/card/{symbol}?date={as_of}", "/json/symbols", "/json/nope",
              "/json/card/LIFE?date=01-09-2026"]
    try:
        for path in probes:
            _status, _ctype, body = _fetch(path)
            if sentinel in body:
                failures.append(f"the key in SECTORS_API_KEY reached the body of {path}")
    finally:
        if before is None:
            os.environ.pop("SECTORS_API_KEY", None)
        else:
            os.environ["SECTORS_API_KEY"] = before
    return failures, len(probes)


def check_metrics_are_the_existing_figures():
    """Every metric must equal the `Figure` `pillars.assess()` built, field for field.

    This is the gate the whole rule rests on: if the surface recomputed anything, the value
    here would be a second derivation of the same quantity, and the fastest way for it to
    drift is for it not to be compared. `value` is compared with `==`, so a float that moved
    by one ulp fails too.
    """
    failures = []
    checked = 0
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        doc = document(source, symbol, as_of, result)
        for pillar, served in zip(result["pillars"], doc["pillars"]):
            for figure, metric in zip(pillar.figures, served["metrics"]):
                checked += 1
                if (metric["name"], metric["value"], metric["unit"], metric["note"],
                        metric["endpoint"], metric["fields"]) != \
                        (figure.name, figure.value, figure.unit, figure.note,
                         figure.endpoint, list(figure.fields)):
                    failures.append(f"{symbol} {as_of} {pillar.name}.{figure.name}: the served "
                                    f"metric is not the figure the pillar built")
        for figure, metric in zip(result.get("modifier_figures") or [], doc["modifier_metrics"]):
            checked += 1
            if metric["name"] != figure.name or metric["value"] != figure.value:
                failures.append(f"{symbol} {as_of} {figure.name}: modifier metric drifted")
        if doc["thresholds"] != result["thresholds"]:
            failures.append(f"{symbol} {as_of}: the threshold provenance is not the one "
                            f"assess() reported")
    return failures, checked + len(P.DEMO_CASES)


def check_json_number_matches_the_text_card():
    """One number, two surfaces: a figure's rendered form must be on the card and in the JSON.

    The card prints `pangsa_puncak 64.7%`; the reply carries the same figure as `0.647`. This
    gate renders the figure with `card._number` — the formatter the card itself uses — and
    requires that string to be on the card text a JSON reply describes. If the two surfaces
    ever read different rows, this is where it shows.
    """
    failures = []
    checked = 0
    for source, symbol, as_of in P.DEMO_CASES:
        result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
        text = card.render(result, source)
        doc = document(source, symbol, as_of, result)
        for pillar, served in zip(result["pillars"], doc["pillars"]):
            for figure, metric in zip(pillar.figures, served["metrics"]):
                if metric["value"] is None:
                    continue
                checked += 1
                rendered = card._number(figure)
                # The card wraps its metric line at WIDTH, so a long rendered value arrives
                # split across two lines with an indent in between. Collapsing runs of
                # whitespace on both sides compares the words the card prints, which is the
                # claim, instead of the column the renderer happened to break at.
                if " ".join(rendered.split()) not in " ".join(text.split()):
                    failures.append(f"{symbol} {as_of} {metric['name']}: the JSON value "
                                    f"renders as {rendered!r}, which is not on the text card")
    return failures, checked


def check_unavailable_fields_are_declared():
    """A field the UI wants but nothing produces must be named, with a reason, and be null.

    The second half is the one that matters: a list that says a field is unavailable while the
    reply quietly carries a value for it is worse than no list at all, because the UI lane
    would read the value and never the note.
    """
    failures = []
    if not UNAVAILABLE:
        return ["no unavailable field is declared"], 1
    source, symbol, as_of = P.DEMO_CASES[0]
    result = P.assess(P.bag_from(source, symbol, as_of), symbol, as_of)
    doc = document(source, symbol, as_of, result)
    checked = 0
    for entry in UNAVAILABLE:
        checked += 1
        if len(entry["reason"]) < 40:
            failures.append(f"{entry['path']}: the reason is too short to audit")
        for node in _walk(doc, entry["path"]):
            if node is not None:
                failures.append(f"{entry['path']}: declared unavailable but the reply "
                                f"carries {node!r}")
    if len(doc["unavailable"]) != len(UNAVAILABLE):
        failures.append("the reply did not carry the whole unavailable list")
    return failures, checked + 1


def _walk(document, path):
    """Every value at a dotted path, walking `[]` over a list. Used by the gate above."""
    nodes = [document]
    for step in path.split("."):
        walk_all = step.endswith("[]")
        key = step[:-2] if walk_all else step
        nxt = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            value = node.get(key)
            if walk_all:
                if isinstance(value, list):
                    nxt.extend(value)
            elif key in node:
                nxt.append(value)
        nodes = nxt
    return nodes


def main():
    total, bad = 0, []
    for check in (check_no_arithmetic_in_this_module, check_imports_are_readers_only,
                  check_response_shape, check_broker_dates_answer_with_a_reason,
                  check_profile_is_the_narrowed_overview,
                  check_determinism, check_no_secret_in_json,
                  check_metrics_are_the_existing_figures,
                  check_json_number_matches_the_text_card,
                  check_unavailable_fields_are_declared):
        failures, count = check()
        total += count
        bad += failures
        print(f"  {check.__name__:<40} {count - len(failures)}/{count}")
    for line in bad:
        print("FAIL", line)
    print(f"{total - len(bad)}/{total} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
