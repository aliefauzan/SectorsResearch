#!/usr/bin/env python3
"""
Five slides in Bahasa Indonesia, and every factual slot names the facts it stands on.

Pure: no I/O, no HTTP, no file paths. Give it a locked FactSet and the three metric
results and it gives back a draft; there is no path through this module by which a number
can appear that did not come out of a fact.

    from template import build_draft, caption

    draft = build_draft(factset, metrics, company_name="Adaro Energy")
    draft["slides"][1]["slots"][0]
    -> {"slot_id": "s2-1", "kind": "factual", "fact_ids": ["a1b2…"],
        "text": "Pendapatan Q1 2026 Rp8,00 T."}

Why a template and not a language model (PRD §21 leaves it open, this resolves it):
a template cannot invent a number. It can still *mislabel* one — narrating a sequential
comparison with year-over-year wording is the exact error this data situation produces —
so `gate.py` stays, and the comparator label travels with every comparing slide.

Three rules the gates below enforce:

  1. A `factual` slot with no `fact_id` is a bug, and it fails here at build time rather
     than at gate time, because a draft that cannot be validated should never exist.
  2. An `unknown` metric is rendered as a sentence that names what is missing and the
     call that would supply it. Never as an omitted slide, never as zero, and never with
     a `%` in it.
  3. A `sign_change` is rendered as two absolute figures. "-340% growth" for a swing from
     profit to loss is arithmetically true and narratively false.

    python3 template.py    # citations, unknowns, sign changes, and the five-slide count
"""
import metrics as metrics_module
import money
import periods

#: Bump when the slide structure or the wording changes. Stamped on every draft, because
#: a claim validated under one template is not validated under another (ER-FR-08).
TEMPLATE_VERSION = "er-carousel-1"

#: Five slides, fixed. ER-FR-01 and PRD §5 make the count a requirement; per-sector
#: templates are ER-FR-16, which is P1 and deliberately not built.
SLIDE_TITLES = (
    "Ringkasan laporan",
    "Pendapatan",
    "Laba bersih",
    "Marjin laba bersih",
    "Sumber dan catatan",
)

#: The call that would make the year-over-year comparator computable. It is quoted in
#: the `unknown` sentence and is never called by anything in this product.
#:
#: `relay.check_endpoint_hint` asserts this string still equals
#: `sources.ENDPOINT["quarterly_yoy"]`, so the two cannot drift apart.
YOY_ENDPOINT_HINT = "/v2/financials/quarterly/{symbol}/?n_quarters=8"

#: What each source is, in one line, on screen and on the terminal. The hackathon rules
#: require synthetic data to be labelled wherever it appears. Verbatim from
#: `src/tunanetra/reader.py:44`.
SOURCE_NOTE = {
    "recorded": ("data asli Sectors, rekaman 6 September 2026 — "
                 "jendela setiap deret dicantumkan"),
    "synth": ("DATA SINTETIS, bukan pasar sungguhan — hanya untuk pengembangan, "
              "tidak pernah menjadi sumber data produk"),
    "mock": "mock lokal di atas rekaman yang sama; nol kredit",
}

DISCLAIMER = ("Alat informasi dan analisis, bukan nasihat investasi. "
              "Tidak ada rekomendasi beli atau jual, dan tidak ada eksekusi transaksi.")

#: Why a comparison could not be made, in a sentence a reviewer can act on. Keyed by the
#: `reason_code` the metric carried.
REASON_SENTENCE = {
    "comparator_unavailable": "periode pembanding {comparator} tidak ada dalam data yang sudah diambil",
    "denominator_zero": "nilai pembanding nol, sehingga pertumbuhan tidak terdefinisi",
    "missing_input": "salah satu angka yang dibutuhkan kosong pada sumber",
    "not_a_number": "salah satu angka datang dalam bentuk yang tidak bisa dibaca sebagai angka",
}

FIELD_LABEL = {"revenue": "Pendapatan", "earnings": "Laba bersih"}

MONTHS = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
          "September", "Oktober", "November", "Desember")


class UncitedSlot(Exception):
    """A factual slot reached a draft without naming a fact.

    Raised at build time. `gate.py` would reject it anyway, but a draft that is already
    known to be invalid should not be written to the database and shown to a reviewer.
    """


def say_date(iso):
    """`"2026-03-31"` -> `"31 Maret 2026"`. Same convention as `src/tunanetra/money.py`."""
    if not iso:
        return None
    try:
        year, month, day = str(iso)[:10].split("-")
        return f"{int(day)} {MONTHS[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return str(iso)


def _slot(slide, index, text, kind="framing", fact_ids=()):
    fact_ids = [f for f in fact_ids if f]
    if kind == "factual" and not fact_ids:
        raise UncitedSlot(f"slide {slide}: {text!r} states a fact and cites nothing")
    return {"slot_id": f"s{slide}-{index}", "slide": slide, "kind": kind,
            "text": text, "fact_ids": fact_ids}


def _fact_id(factset, role, field):
    for fact in factset["facts"]:
        if fact["role"] == role and fact["field"] == field:
            return fact["fact_id"]
    return None


def _value(factset, role, field):
    for fact in factset["facts"]:
        if fact["role"] == role and fact["field"] == field:
            return fact["normalized_value"]
    return None


def _report_date(factset, role="target"):
    for fact in factset["facts"]:
        if fact["role"] == role:
            row = (factset.get("rows") or {}).get(fact["period"]) or {}
            return row.get("report_date")
    return None


def _comparison_slots(slide, factset, result, field, comparator):
    """The two or three slots that carry one metric. The whole point of the module."""
    slots = []
    label = FIELD_LABEL[field]
    target_id = _fact_id(factset, "target", field)
    prior_id = _fact_id(factset, "comparator", field)
    target_value = _value(factset, "target", field)
    prior_value = _value(factset, "comparator", field)
    period = periods.quarter_label(factset["period_key"])

    slots.append(_slot(slide, 1,
                       f"{label} {period} {money.rupiah(target_value)}.",
                       kind="factual", fact_ids=[target_id]))

    mode = comparator.get("mode", "yoy")
    if result["status"] == metrics_module.OK:
        direction = metrics_module.direction(result["value"])
        magnitude = (result["display"] or "").lstrip("-")
        slots.append(_slot(
            slide, 2,
            f"{direction.capitalize()} {magnitude} dari {money.rupiah(prior_value)} "
            f"pada {periods.quarter_label(comparator['key'])}.",
            kind="factual", fact_ids=[target_id, prior_id]))
    elif result["status"] == metrics_module.SIGN_CHANGE:
        # Two magnitudes and the words for the swing. No growth rate exists here.
        slots.append(_slot(
            slide, 2,
            f"Berbalik arah: {money.signed_rupiah(prior_value)} pada "
            f"{periods.quarter_label(comparator['key'])} menjadi "
            f"{money.signed_rupiah(target_value)}. Persentase pertumbuhan tidak "
            f"ditampilkan karena tandanya berubah.",
            kind="factual", fact_ids=[target_id, prior_id]))
    else:
        reason = REASON_SENTENCE.get(result["reason_code"], "pembanding tidak tersedia")
        reason = reason.format(comparator=periods.quarter_label(comparator["key"])
                               if comparator.get("key") else "sebelumnya")
        slots.append(_slot(
            slide, 2,
            f"Perbandingan belum bisa dihitung: {reason}. Panggilan yang "
            f"menyediakannya: {YOY_ENDPOINT_HINT.format(symbol=factset['symbol'])}.",
            kind="factual", fact_ids=[target_id]))

    slots.append(_slot(slide, 3, periods.label_sentence(mode) + "."))
    return slots


def build_draft(factset, results, company_name=None):
    """One draft from one locked FactSet. `results` is `{metric_type: result}`."""
    factset = dict(factset) if not isinstance(factset, dict) else factset
    comparator = dict(factset["comparator"])
    symbol = factset["symbol"]
    period = periods.quarter_label(factset["period_key"])
    slides = []

    # ------------------------------------------------------------- 1. the report
    name = f"{company_name} ({symbol})" if company_name else symbol
    slots = [_slot(1, 1, f"{name} — laporan keuangan {period}.")]
    report_date = _report_date(factset)
    if report_date:
        slots.append(_slot(1, 2,
                           f"Tanggal akhir periode {say_date(report_date)}.",
                           kind="factual",
                           fact_ids=[_fact_id(factset, "target", "revenue")]))
    slots.append(_slot(1, 3, "Draf untuk ditinjau. Belum dipublikasikan."))
    slides.append({"index": 1, "title": SLIDE_TITLES[0], "slots": slots})

    # -------------------------------------------------- 2, 3, 4. the three metrics
    slides.append({"index": 2, "title": SLIDE_TITLES[1],
                   "slots": _comparison_slots(2, factset, results["revenue_yoy"],
                                              "revenue", comparator)})
    slides.append({"index": 3, "title": SLIDE_TITLES[2],
                   "slots": _comparison_slots(3, factset, results["net_income_yoy"],
                                              "earnings", comparator)})

    margin = results["net_margin_delta"]
    margin_slots = []
    target_ids = [_fact_id(factset, "target", "earnings"),
                  _fact_id(factset, "target", "revenue")]
    if margin["status"] == metrics_module.OK:
        current = _value(factset, "target", "earnings") / _value(factset, "target", "revenue")
        margin_slots.append(_slot(
            4, 1,
            f"Marjin laba bersih {period} {metrics_module.round_display(current)}.",
            kind="factual", fact_ids=target_ids))
        direction = metrics_module.direction(margin["value"])
        margin_slots.append(_slot(
            4, 2,
            f"{direction.capitalize()} {(margin['display'] or '').lstrip('-')} "
            f"dibanding {periods.quarter_label(comparator['key'])}.",
            kind="factual",
            fact_ids=target_ids + [_fact_id(factset, "comparator", "earnings"),
                                   _fact_id(factset, "comparator", "revenue")]))
    else:
        reason = REASON_SENTENCE.get(margin["reason_code"], "pembanding tidak tersedia")
        reason = reason.format(comparator=periods.quarter_label(comparator["key"])
                               if comparator.get("key") else "sebelumnya")
        margin_slots.append(_slot(
            4, 1,
            f"Perubahan marjin belum bisa dihitung: {reason}. Panggilan yang "
            f"menyediakannya: {YOY_ENDPOINT_HINT.format(symbol=symbol)}.",
            kind="factual", fact_ids=target_ids))
    margin_slots.append(_slot(4, 3,
                              periods.label_sentence(comparator["mode"])
                              + ". Selisih marjin dinyatakan dalam poin persentase."))
    slides.append({"index": 4, "title": SLIDE_TITLES[3], "slots": margin_slots})

    # ------------------------------------------------------------- 5. the provenance
    endpoint = (factset.get("endpoint") or "").format(symbol=symbol)
    slides.append({"index": 5, "title": SLIDE_TITLES[4], "slots": [
        _slot(5, 1, f"Sumber: Sectors, {endpoint}, per {factset['as_of']}."),
        _slot(5, 2, SOURCE_NOTE.get(factset["source"], factset["source"])),
        _slot(5, 3, DISCLAIMER),
    ]})

    draft = {
        "template_version": TEMPLATE_VERSION,
        "symbol": symbol,
        "period_key": factset["period_key"],
        "fact_set_id": factset["fact_set_id"],
        "fact_set_version": factset["version"],
        "comparator": comparator,
        "source": factset["source"],
        "as_of": factset["as_of"],
        "slides": slides,
    }
    draft["caption"] = caption(draft)
    return draft


def caption(draft):
    """The slides as one paragraph, for the review queue preview and the clipboard."""
    lines = []
    for slide in draft["slides"]:
        lines.append(" ".join(slot["text"] for slot in slide["slots"]))
    return "\n\n".join(lines)


def slots_of(draft):
    """Every slot in slide order. Nothing walks `slides` by index."""
    return [slot for slide in draft["slides"] for slot in slide["slots"]]


def factual_slots(draft):
    return [slot for slot in slots_of(draft) if slot["kind"] == "factual"]


# ------------------------------------------------------------------------------ gates


def _factset(revenue=8004471444300, earnings=2178080414220,
             prior_revenue=8792499261000, prior_earnings=2445263751840,
             comparator_status="ok", mode="sequential"):
    import factset as factset_module

    def row(period, date, rev, ni):
        return {"symbol": "ADRO", "report_date": date, "period_key": period,
                "quarter_label_seen": None, "capex": 1000,
                "capex_source_field": "capital_expenditure", "source": "recorded",
                "revenue": rev, "earnings": ni, "gross_profit": 1, "operating_pnl": 2,
                "total_assets": 3, "total_equity": 4, "total_liabilities": 5,
                "operating_cash_flow": 6}

    rows = {"q1-2026": row("q1-2026", "2026-03-31", revenue, earnings)}
    comparator_key = "q4-2025" if mode == "sequential" else "q1-2025"
    if comparator_status == "ok":
        rows[comparator_key] = row(comparator_key, "2025-12-31", prior_revenue,
                                   prior_earnings)
    comparator = {"mode": mode, "key": comparator_key, "status": comparator_status,
                  "reason_code": None if comparator_status == "ok"
                  else "comparator_unavailable"}
    return factset_module.build_factset(
        "ADRO", "q1-2026", rows, comparator, "recorded",
        "/v2/financials/quarterly/{symbol}/?n_quarters=4", "2026-09-06",
        now="2026-09-10T00:00:00")


def _results(factset, comparator_status="ok"):
    facts = {(f["role"], f["field"]): f["normalized_value"] for f in factset["facts"]}
    mode = factset["comparator"]["mode"]
    if comparator_status != "ok":
        return {t: metrics_module.unavailable(t, mode, "comparator_unavailable")
                for t in metrics_module.METRIC_TYPES}
    return {
        "revenue_yoy": metrics_module.revenue_yoy(
            facts[("target", "revenue")], facts[("comparator", "revenue")], mode),
        "net_income_yoy": metrics_module.net_income_yoy(
            facts[("target", "earnings")], facts[("comparator", "earnings")], mode),
        "net_margin_delta": metrics_module.net_margin_delta(
            facts[("target", "earnings")], facts[("target", "revenue")],
            facts[("comparator", "earnings")], facts[("comparator", "revenue")], mode),
    }


def check_citations():
    """Every factual slot cites a fact, and every cited fact exists in the FactSet."""
    failures = []
    factset = _factset()
    draft = build_draft(factset, _results(factset), company_name="Adaro Energy")
    known = {f["fact_id"] for f in factset["facts"]}

    for slot in factual_slots(draft):
        if not slot["fact_ids"]:
            failures.append(f"{slot['slot_id']}: factual slot with no fact_id")
        for fact_id in slot["fact_ids"]:
            if fact_id not in known:
                failures.append(f"{slot['slot_id']}: cites unknown fact {fact_id}")
    if not factual_slots(draft):
        failures.append("the draft has no factual slots at all")

    # A factual slot built with no fact must fail here, not at gate time.
    try:
        _slot(2, 9, "Pendapatan naik.", kind="factual", fact_ids=[])
    except UncitedSlot:
        pass
    else:
        failures.append("an uncited factual slot was built")

    if len(draft["slides"]) != 5:
        failures.append(f"{len(draft['slides'])} slides, expected 5")
    if [s["title"] for s in draft["slides"]] != list(SLIDE_TITLES):
        failures.append("the slide titles moved")
    if draft["template_version"] != TEMPLATE_VERSION:
        failures.append("the draft is not stamped with a template version")
    return failures, len(factual_slots(draft)) + 4


def check_numbers_come_from_facts():
    """Every rupiah figure on a slide is a figure that is in the FactSet."""
    failures = []
    factset = _factset()
    draft = build_draft(factset, _results(factset))
    values = [f["normalized_value"] for f in factset["facts"]
              if f["normalized_value"] is not None]

    for slot in factual_slots(draft):
        # The endpoint hint contains `n_quarters=8`, which is a parameter and not a sum.
        text = slot["text"].replace(YOY_ENDPOINT_HINT.format(symbol="ADRO"), "")
        for magnitude in money.magnitudes(text):
            if not any(money.close_enough(magnitude, value) for value in values):
                failures.append(f"{slot['slot_id']}: {magnitude} is on the slide and "
                                f"in no fact")
    return failures, len(factual_slots(draft))


def check_unknown_rendering():
    """An unknown metric names what is missing and the call that would supply it."""
    failures = []
    factset = _factset(comparator_status="unavailable", mode="yoy")
    draft = build_draft(factset, _results(factset, "unavailable"))
    text = caption(draft)

    if "%" in text:
        failures.append("an unknown metric rendered a percentage")
    if "?n_quarters=8" not in text:
        failures.append("the unknown sentence does not name the call that would fix it")
    if "belum bisa dihitung" not in text:
        failures.append("the unknown sentence does not say the comparison is missing")
    if "Q1 2025" not in text:
        failures.append("the unknown sentence does not name the missing period")
    if len(draft["slides"]) != 5:
        failures.append("an unknown metric dropped a slide instead of explaining itself")
    if "0,0%" in text or "Rp0" in text:
        failures.append("an unknown metric became a zero")
    # The comparator label must still be there, and it must be the yoy one.
    if periods.label_sentence("yoy") not in text:
        failures.append("the comparator label is missing from an unknown comparison")
    return failures, 7


def check_sign_change_rendering():
    """A profit that became a loss is two magnitudes, never a growth percentage."""
    failures = []
    factset = _factset(earnings=-500_000_000_000)
    results = _results(factset)
    if results["net_income_yoy"]["status"] != metrics_module.SIGN_CHANGE:
        failures.append("the fixture no longer produces a sign change")
    draft = build_draft(factset, results)
    slide = draft["slides"][2]
    text = " ".join(slot["text"] for slot in slide["slots"])
    if "Berbalik arah" not in text:
        failures.append("the sign change is not announced")
    if "%" in text:
        failures.append("a sign change rendered a percentage")
    if "minus Rp500,00 M" not in text:
        failures.append(f"the loss is not shown as an absolute figure: {text}")
    return failures, 4


def check_comparator_label():
    """Every comparing slide carries the label for the comparator it actually used."""
    failures = []
    for mode in ("sequential", "yoy"):
        factset = _factset(mode=mode)
        draft = build_draft(factset, _results(factset))
        label = periods.label_sentence(mode)
        for slide in draft["slides"][1:4]:
            text = " ".join(slot["text"] for slot in slide["slots"])
            if label not in text:
                failures.append(f"{mode}: slide {slide['index']} has no comparator label")
        if mode == "sequential":
            spoken = caption(draft).lower()
            for word in periods.YOY_WORDING:
                # The one that protects the recorded demo from lying.
                if word in spoken:
                    failures.append(f"sequential draft contains YoY wording: {word!r}")
    return failures, 6 + len(periods.YOY_WORDING)


def check_labelling():
    """Source note and disclaimer on every draft; synthetic data labelled as such."""
    failures = []
    factset = _factset()
    draft = build_draft(factset, _results(factset))
    text = caption(draft)
    if DISCLAIMER not in text:
        failures.append("the disclaimer is missing")
    if SOURCE_NOTE["recorded"] not in text:
        failures.append("the source note is missing")
    if "/v2/financials/quarterly/ADRO/" not in text:
        failures.append("the draft does not name the endpoint it was built from")
    if factset["as_of"] not in text:
        failures.append("the draft does not state its as_of")

    synth = dict(_factset())
    synth["source"] = "synth"
    synth_draft = build_draft(synth, _results(synth))
    if "SINTETIS" not in caption(synth_draft):
        failures.append("a synthetic draft is not labelled DATA SINTETIS")
    return failures, 5


def main():
    results = [("citations", *check_citations()),
               ("numbers from facts", *check_numbers_come_from_facts()),
               ("unknown rendering", *check_unknown_rendering()),
               ("sign change", *check_sign_change_rendering()),
               ("comparator label", *check_comparator_label()),
               ("labelling", *check_labelling())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nno number reaches a slide without the fact it came from" if not failed
          else f"\n{failed} template failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
