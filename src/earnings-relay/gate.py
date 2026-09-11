#!/usr/bin/env python3
"""
The Claim Risk Gate: every factual sentence checked against the facts it cites.

Pure: no I/O, no HTTP, no file paths. It takes a claim, the locked FactSet and the metric
results, and returns one of `supported`, `needs_review`, `rejected` with the reason codes
that produced it (ER-FR-09).

    from gate import check_claim, validate_draft

    check_claim(claim, factset, results)
    -> ("rejected", ["comparator_mislabelled"])

Seven checks, in the order a reviewer would run them:

  * `no_fact_id`             a factual claim that cites nothing. Rejected, full stop
                             (PRD §9) — there is no version of this that is merely risky.
  * `unknown_fact_id`        a claim citing a fact that is not in this FactSet. Usually a
                             stale claim after a restatement, which is exactly AT-05.
  * `number_mismatch`        a figure in the text that is not a figure in the cited facts.
  * `period_mismatch`        a period named in the text that the FactSet is not about.
  * `direction_mismatch`     "naik"/"turun" against `metrics.direction()` on the
                             UNROUNDED value.
  * `comparator_mislabelled` year-over-year wording beside a sequential comparator. On
                             recorded data this is the only comparison that is
                             computable, so this check is what stops the demo lying.
  * `prohibited_phrase`      transaction invitations, price targets, unbacked
                             superlatives, plus whatever the Admin added.

And one that downgrades rather than rejects: `unknown_metric_narrated` puts a claim
standing on an `unknown` or `sign_change` metric into `needs_review`, so approval is
blocked until a human has looked at it (AT-08).

A gate that only ever passes is not tested, so the gate below runs one adversarial draft
per reason code — the `--broken` idiom from `src/tunanetra/a11y_check.py`.

    python3 gate.py    # one rejection per reason code, plus one clean draft
"""
import itertools
import re

import metrics as metrics_module
import money
import periods
import template

SUPPORTED = "supported"
NEEDS_REVIEW = "needs_review"
REJECTED = "rejected"

NO_FACT_ID = "no_fact_id"
UNKNOWN_FACT_ID = "unknown_fact_id"
NUMBER_MISMATCH = "number_mismatch"
PERIOD_MISMATCH = "period_mismatch"
DIRECTION_MISMATCH = "direction_mismatch"
COMPARATOR_MISLABELLED = "comparator_mislabelled"
PROHIBITED_PHRASE = "prohibited_phrase"
UNKNOWN_METRIC_NARRATED = "unknown_metric_narrated"

#: Anything in here rejects. Nothing in here is a matter of taste.
#:
#: The first block is `narrate.ADVICE_VOCAB` from `src/tunanetra/narrate.py:288`, which
#: is already gate-tested in that product; the rest is what a caption written by a person
#: in the review queue actually reaches for. PRD §9: transaction invitations, price
#: targets, superlatives with no basis.
PROHIBITED = (
    # advice, seeded from the sibling product
    "beli sekarang", "jual sekarang", "sebaiknya beli", "sebaiknya jual",
    "target harga", "rekomendasi beli", "rekomendasi jual", "cut loss",
    "take profit", "should buy", "should sell", "price target",
    # transaction invitations
    "beli", "jual", "akumulasi", "entry", "cuan", "boncos", "hold", "buyback saham anda",
    # price targets
    "tp", "stop loss", "support kuat", "resistance kuat",
    # superlatives with no basis
    "terbaik", "paling untung", "pasti", "dijamin", "saham unggulan", "wajib punya",
    # a compliance verdict is not this product's to give
    "sesuai ketentuan", "compliant", "aman secara hukum",
)

#: Text that is allowed to contain prohibited wording, because its whole job is to rule
#: it out. Matched by identity, never by pattern — the same trick as
#: `reader.check_no_advice`, which scans the derived sentences rather than the page so
#: that the disclaimer does not flag itself.
EXEMPT = (template.DISCLAIMER,)

#: Which metric each slide stands on. Slides 1 and 5 make no comparison.
SLIDE_METRIC = {2: "revenue_yoy", 3: "net_income_yoy", 4: "net_margin_delta"}

DIRECTION_WORDS = ("naik", "turun", "datar")

_PERIOD_IN_TEXT = re.compile(r"\b(?:q([1-4])-(\d{4})|Q([1-4])\s+(\d{4}))\b",
                             re.IGNORECASE)


def _words(text):
    return (text or "").lower()


def periods_in(text):
    """Every period this text names, as period keys. `"Q1 2026"` and `"q1-2026"` both."""
    out = []
    for match in _PERIOD_IN_TEXT.finditer(text or ""):
        quarter = match.group(1) or match.group(3)
        year = match.group(2) or match.group(4)
        out.append(f"q{quarter}-{year}")
    return out


def directions_in(text):
    """Every direction word in the text, lowercased, in order."""
    spoken = _words(text)
    return [word for word in DIRECTION_WORDS
            if re.search(rf"\b{word}\b", spoken)]


def _cited_values(factset, fact_ids):
    values = []
    unknown = []
    known = {f["fact_id"]: f for f in factset["facts"]}
    for fact_id in fact_ids:
        fact = known.get(fact_id)
        if fact is None:
            unknown.append(fact_id)
            continue
        if fact["normalized_value"] is not None:
            values.append(fact["normalized_value"])
    return values, unknown


def _rate_candidates(values, result):
    """Every rate a claim standing on these facts is allowed to state.

    The metric's own value, plus any ratio of two cited facts — a margin is a ratio of
    two facts on the same slide and is not itself a metric, so refusing it would make the
    honest sentence unwritable.
    """
    candidates = []
    if result and result.get("value") is not None:
        candidates.append(abs(result["value"]))
    for first, second in itertools.permutations(values, 2):
        if second:
            candidates.append(abs(first / second))
    return candidates


def check_claim(claim, factset, results, prohibited_extra=(), comparator=None):
    """`(status, [reason_codes])` for one claim. The only entry point that matters."""
    reasons = []
    text = claim.get("text") or ""
    kind = claim.get("kind", "framing")
    fact_ids = list(claim.get("fact_ids") or ())
    comparator = comparator or ((factset or {}).get("comparator") or {})
    result = results.get(SLIDE_METRIC.get(claim.get("slide"))) if results else None

    # ------------------------------------------------------------ prohibited wording
    if text not in EXEMPT:
        spoken = _words(text)
        for phrase in tuple(PROHIBITED) + tuple(prohibited_extra):
            if re.search(rf"\b{re.escape(phrase.lower())}\b", spoken):
                reasons.append(PROHIBITED_PHRASE)
                break

    # ------------------------------------------------------------ comparator honesty
    # Checked on every kind of slot: a framing line that says "YoY" beside a sequential
    # comparison is exactly as false as a factual one that does.
    if comparator.get("mode") == "sequential":
        spoken = _words(text)
        if any(word in spoken for word in periods.YOY_WORDING):
            reasons.append(COMPARATOR_MISLABELLED)

    if kind != "factual":
        status = REJECTED if reasons else SUPPORTED
        return status, sorted(set(reasons))

    # ------------------------------------------------------------------- fact linkage
    if not fact_ids:
        return REJECTED, sorted(set(reasons + [NO_FACT_ID]))
    values, unknown = _cited_values(factset, fact_ids)
    if unknown:
        reasons.append(UNKNOWN_FACT_ID)

    # ------------------------------------------------------------------------ numbers
    for magnitude in money.magnitudes(text):
        # Compared on magnitude, not on sign: a loss is written "minus Rp500,00 M", so
        # the sign lives in a word rather than in the numeral. Whether the sign is the
        # right way round is `direction_mismatch`'s job, and a sign change is rendered
        # with both figures spelled out (`template._comparison_slots`).
        if not any(money.close_enough(abs(magnitude), abs(value)) for value in values):
            reasons.append(NUMBER_MISMATCH)
            break

    rates = money.percentages(text) + money.points(text)
    if rates:
        candidates = _rate_candidates(values, result)
        for rate in rates:
            # `close_rate`, not `close_enough`: a rate is compared at the precision it
            # was displayed at, which is one decimal place in percent.
            if not any(money.close_rate(abs(rate), candidate)
                       for candidate in candidates):
                reasons.append(NUMBER_MISMATCH)
                break

    # ------------------------------------------------------------------------ periods
    allowed = {factset.get("period_key"), comparator.get("key")}
    for named in periods_in(text):
        if named not in allowed:
            reasons.append(PERIOD_MISMATCH)
            break

    # --------------------------------------------------------------------- directions
    spoken_directions = directions_in(text)
    if spoken_directions:
        if result is None or result.get("value") is None:
            # A direction word on a comparison that produced no value at all.
            reasons.append(DIRECTION_MISMATCH)
        else:
            true_direction = metrics_module.direction(result["value"])
            if any(word != true_direction for word in spoken_directions):
                reasons.append(DIRECTION_MISMATCH)

    if reasons:
        return REJECTED, sorted(set(reasons))

    # --------------------------------------------------- honest but not yet resolved
    if result is not None and result.get("status") in (metrics_module.UNKNOWN,
                                                       metrics_module.SIGN_CHANGE):
        return NEEDS_REVIEW, [UNKNOWN_METRIC_NARRATED]
    return SUPPORTED, []


def validate_draft(draft, factset, results, prohibited_extra=()):
    """Every slot in a draft as a claim row, ready for `store.save_claims`."""
    comparator = draft.get("comparator") or factset.get("comparator") or {}
    claims = []
    for slot in template.slots_of(draft):
        claim = {"claim_id": f"{draft['fact_set_id']}-{slot['slot_id']}",
                 "slide": slot["slide"], "text": slot["text"], "kind": slot["kind"],
                 "fact_ids": list(slot["fact_ids"])}
        status, reasons = check_claim(claim, factset, results, prohibited_extra,
                                      comparator)
        claim["validation_status"] = status
        claim["reason_codes"] = reasons
        claims.append(claim)
    return claims


def unresolved(claims):
    """The claims that block approval (AT-08): anything not `supported`."""
    return [c for c in claims if c["validation_status"] != SUPPORTED]


# ------------------------------------------------------------------------------ gates


def _fixture(**kwargs):
    """A real locked FactSet plus its metric results, built the way `relay.py` does."""
    factset = template._factset(**kwargs)
    results = template._results(
        factset, "ok" if kwargs.get("comparator_status", "ok") == "ok" else "unavailable")
    draft = template.build_draft(factset, results, company_name="Adaro Energy")
    return factset, results, draft


def _claim(text, kind="factual", fact_ids=(), slide=2):
    return {"claim_id": "c1", "slide": slide, "text": text, "kind": kind,
            "fact_ids": list(fact_ids)}


def check_clean_draft():
    """The template's own output must pass. If it does not, one of the two is wrong."""
    failures = []
    factset, results, draft = _fixture()
    claims = validate_draft(draft, factset, results)
    for claim in claims:
        if claim["validation_status"] != SUPPORTED:
            failures.append(f"{claim['claim_id']}: {claim['validation_status']} "
                            f"{claim['reason_codes']} — {claim['text']}")
    if not claims:
        failures.append("the clean draft produced no claims at all")
    if unresolved(claims):
        failures.append("a clean draft would block approval")
    print(f"        clean draft · {len(claims)} klaim, semua supported")
    return failures, len(claims) + 2


def check_adversarial():
    """One hand-written draft per reason code. A gate that only passes is not tested."""
    failures = []
    factset, results, _ = _fixture()
    revenue_fact = template._fact_id(factset, "target", "revenue")
    prior_fact = template._fact_id(factset, "comparator", "revenue")

    cases = [
        # (claim, expected status, expected reason, why)
        (_claim("Pendapatan Q1 2026 Rp8,00 T.", fact_ids=[]),
         REJECTED, NO_FACT_ID, "a factual claim citing nothing"),
        (_claim("Pendapatan Q1 2026 Rp8,00 T.", fact_ids=["deadbeef1234"]),
         REJECTED, UNKNOWN_FACT_ID, "a claim citing a fact from another FactSet"),
        (_claim("Pendapatan Q1 2026 Rp9,00 T.", fact_ids=[revenue_fact]),
         REJECTED, NUMBER_MISMATCH, "a figure that is not the cited fact"),
        (_claim("Turun 25,0% dari Rp8,79 T pada Q4 2025.",
                fact_ids=[revenue_fact, prior_fact]),
         REJECTED, NUMBER_MISMATCH, "a growth rate that is not the metric"),
        (_claim("Pendapatan Q3 2024 Rp8,00 T.", fact_ids=[revenue_fact]),
         REJECTED, PERIOD_MISMATCH, "a period this FactSet is not about"),
        (_claim("Naik 9,0% dari Rp8,79 T pada Q4 2025.",
                fact_ids=[revenue_fact, prior_fact]),
         REJECTED, DIRECTION_MISMATCH, "a fall narrated as a rise"),
        (_claim("Turun 9,0% YoY dari Rp8,79 T pada Q4 2025.",
                fact_ids=[revenue_fact, prior_fact]),
         REJECTED, COMPARATOR_MISLABELLED, "a sequential comparison called YoY"),
        (_claim("Pendapatan turun tetapi tahun lalu lebih baik.", kind="framing"),
         REJECTED, COMPARATOR_MISLABELLED, "YoY wording in a framing line"),
        (_claim("Target harga 9000 setelah laporan ini.", fact_ids=[revenue_fact]),
         REJECTED, PROHIBITED_PHRASE, "a price target"),
        (_claim("Saham terbaik kuartal ini, wajib punya.", fact_ids=[revenue_fact]),
         REJECTED, PROHIBITED_PHRASE, "an unbacked superlative"),
        (_claim("Beli sekarang sebelum naik lagi.", fact_ids=[revenue_fact]),
         REJECTED, PROHIBITED_PHRASE, "a transaction invitation"),
        (_claim("Draf ini sudah sesuai ketentuan.", kind="framing"),
         REJECTED, PROHIBITED_PHRASE, "a compliance verdict"),
    ]
    for claim, expected_status, expected_reason, why in cases:
        status, reasons = check_claim(claim, factset, results)
        if status != expected_status:
            failures.append(f"{why}: status {status}, expected {expected_status}")
        if expected_reason not in reasons:
            failures.append(f"{why}: reasons {reasons}, expected {expected_reason}")

    # Every reason code this module defines must be exercised by the table above.
    exercised = {reason for _, _, reason, _ in cases}
    defined = {NO_FACT_ID, UNKNOWN_FACT_ID, NUMBER_MISMATCH, PERIOD_MISMATCH,
               DIRECTION_MISMATCH, COMPARATOR_MISLABELLED, PROHIBITED_PHRASE}
    if defined - exercised:
        failures.append(f"reason codes never tested: {sorted(defined - exercised)}")
    print(f"        adversarial · {len(cases)} draf ditolak, "
          f"{len(exercised)} reason code")
    return failures, len(cases) + 1


def check_unknown_downgrade():
    """An honest unknown is not a rejection — it is a claim a human has to resolve."""
    failures = []
    factset, results, draft = _fixture(comparator_status="unavailable", mode="yoy")
    claims = validate_draft(draft, factset, results)

    downgraded = [c for c in claims
                  if c["validation_status"] == NEEDS_REVIEW
                  and UNKNOWN_METRIC_NARRATED in c["reason_codes"]]
    if len(downgraded) < 3:
        failures.append(f"{len(downgraded)} claims went to needs_review on an "
                        f"unavailable comparator, expected one per metric slide")
    if any(c["validation_status"] == REJECTED for c in claims):
        failures.append("an honest unknown was rejected rather than downgraded")
    if not unresolved(claims):
        failures.append("a draft with three unknown metrics would not block approval")

    # A sign change is also a human decision, not a rejection.
    sign_factset, sign_results, sign_draft = _fixture(earnings=-500_000_000_000)
    sign_claims = validate_draft(sign_draft, sign_factset, sign_results)
    slide_three = [c for c in sign_claims if c["slide"] == 3 and c["kind"] == "factual"]
    if not any(c["validation_status"] == NEEDS_REVIEW for c in slide_three):
        failures.append("a sign change did not require review")
    if any(c["validation_status"] == REJECTED for c in sign_claims):
        failures.append(f"a sign change was rejected: "
                        f"{[c['reason_codes'] for c in sign_claims if c['validation_status'] == REJECTED]}")
    print(f"        unknown · {len(downgraded)} klaim needs_review, 0 rejected")
    return failures, 5


def check_parsers():
    """The three text parsers, each on the string that would fool a naive version."""
    failures = []
    if periods_in("Pendapatan Q1 2026 turun dari q4-2025.") != ["q1-2026", "q4-2025"]:
        failures.append(f"periods_in: {periods_in('Q1 2026 dan q4-2025')}")
    if periods_in("Rp8,00 T pada 31 Maret 2026"):
        failures.append("a date was read as a period")
    if directions_in("Turun 9,0% dari Rp8,79 T.") != ["turun"]:
        failures.append("directions_in missed a capitalised direction word")
    if directions_in("Kenaikan biaya menurunkan laba"):
        failures.append("directions_in matched inside a longer word")
    if directions_in("Naik lalu turun") != ["naik", "turun"]:
        failures.append("directions_in missed a second direction word")
    # The disclaimer must never flag itself.
    status, reasons = check_claim(_claim(template.DISCLAIMER, kind="framing"), None, None)
    if status != SUPPORTED:
        failures.append(f"the disclaimer flagged itself: {reasons}")
    return failures, 6


def main():
    results = [("clean draft", *check_clean_draft()),
               ("adversarial drafts", *check_adversarial()),
               ("unknown downgrade", *check_unknown_downgrade()),
               ("text parsers", *check_parsers())]

    failed = 0
    for name, failures, checked in results:
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  {name:22} {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        failed += len(failures)
    print("\nevery reason code rejects something, and the honest draft passes"
          if not failed else f"\n{failed} gate failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
