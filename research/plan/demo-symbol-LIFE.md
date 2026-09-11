# Demo symbol — LIFE.JK, captured live 11 September 2026

Seven credits, one symbol, every call one that `pillars.bag_from()` actually performs.
Plan: [`../harness/plans/plan-katalis-life.json`](../harness/plans/plan-katalis-life.json).
Ledger: `../harness/recorded/_ledger.jsonl`, last seven rows.

## Why this symbol

Selected for **zero credits** by crossing two payloads already on disk.

| Evidence | Source | Value |
| --- | --- | --- |
| Thinnest free float of any top-changes gainer | `recorded/v2_free-float.json` (961 rows) | **0.075** |
| Move | `recorded/v2_companies_top-changes.json` | +50.6% 7d, +124.2% 14d, +118.5% 30d |
| Two exchange suspensions | `recorded/v2_suspensions.json` | **2026-09-02** and **2026-09-04**, both "peningkatan harga kumulatif yang signifikan … cooling down" |

The suspensions are what make this a **labeled event** rather than a mover: the card
either raised a pillar before 2026-09-02 or it did not, and that is checkable from the repo.

## What the card does, on real IDX data

`./run.sh pilar LIFE 2026-09-01` — the last trading day before the first suspension:

```
SATU PEMBELI DOMINAN  ·  FLOAT TIPIS · free float 7.5%
LIFE · PT MSIG Life Insurance Indonesia Tbk 2026-08-28..2026-09-01 · recorded
!! KONSENTRASI  Satu broker, XL (Stockbit Sekuritas Digital), mengambil 65% dari net beli.
!! VOLUME      Volume puncak 4.2 z di atas kebiasaannya sendiri (45 hari bursa).
!! MOMENTUM    Naik +41.7% dalam 3 hari bursa; +41.1% setelah gerak IHSG dikeluarkan, 16.7 z.
 · KATALIS     Ada kabar yang mendahului … (2026-08-21).
```

### Warning timeline against the exchange's own action

| as-of | verdict | konsentrasi |
| --- | --- | --- |
| 2026-08-26 | SATU PILAR MENYALA | tenang |
| **2026-08-27** | **SATU PEMBELI DOMINAN** | **bahaya** |
| 2026-08-28 | SATU PILAR MENYALA | waspada |
| 2026-08-31 | SATU PEMBELI DOMINAN | bahaya |
| 2026-09-01 | SATU PEMBELI DOMINAN | bahaya |
| **2026-09-02** | — | **IDX suspends LIFE.JK** |
| 2026-09-03 | SATU PEMBELI DOMINAN | bahaya |
| **2026-09-04** | — | **IDX suspends LIFE.JK again** |

Top verdict first reached **2026-08-27, four trading days before the exchange acted**.

### What the tape says that no news feed does

The dominant buyer is **XL, Stockbit Sekuritas Digital** — a retail app — and the cohort
split on the same window is **retail 65%, institutional 28%, mixed 7%**. A 7.5%-float
insurance company moved 41% in three sessions on retail order flow through one broker.
That sentence comes from joining `/v2/broker-summary/LIFE/` against the cached
`/v2/brokers/` registry, at zero extra credit, and it exists in no news feed.

## Facts settled by this capture

| Claim | Result |
| --- | --- |
| `/v2/daily/` "caps at 90 days" | **90 *calendar* days, not 90 trading days.** Requested 2026-05-01→2026-09-10, received 2026-06-12→2026-09-10 — 91 calendar days, **62 trading rows**. `baseline_days` 45 + `event_window` 3 + a 10-day scan = 58, so it fits, with four rows to spare. The threshold note in `thresholds.py` should say calendar. |
| `/v2/index-daily/ihsg/` window | Same truncation, same 62 rows. The previously recorded ihsg payload held only 20. |
| `?sections=financials` bills 1, not 8 | **Confirmed.** Payload came back with exactly three top-level keys — `symbol`, `company_name`, `financials`. `outstanding_shares` present for 2018–2025; 2025 = 2,104,367,347. |
| Broker-summary 14-day guard | 2026-08-22→2026-09-04 returned **7 trading days**, 2026-08-24→2026-09-03. Still no documented limit; the guard held. |
| Registry join completeness | **32 broker codes in the LIFE tape, 32 mapped, zero unmapped** — cleaner than BBCA's 85/84. |
| `/v2/filings/?symbol=LIFE.JK` | `total_count: 0`. No material filing explains the move. Billed 1 credit for a true negative. |
| API returns cost headers | **No.** `cost_headers` is `{}` on all seven calls, so `billed_cost` in the ledger is the harness's estimate and only the portal usage log can confirm it. |

### The 91-credit gap JURI-v6 flagged is explained

`est_cost` 363 versus `billed_cost` 272. Decomposed from the ledger:

- **27 credits** estimated for calls that never billed — 20×400, 6×403, 1×405, all free failures.
- **64 credits** of over-estimation on calls that did bill — 336 estimated against 272 charged,
  mostly the company-report default-8 and free-float per-100 rules being applied conservatively.

Not a mystery, but still an estimate: with no cost headers, reconcile against the portal.

## Known weakness this capture exposes

Pilar Katalis returns **tenang** here, citing a 2026-08-21 article about death claims as
"kabar yang mendahului". An article about claims experience does not explain a 41% run.
The temporal split (before/after) is arithmetic and works; the **explains-versus-reports**
judgment is Fase 4 and is not built, so the pillar currently under-warns on exactly the
case the product exists for. The two articles inside the window are a
"Top Gainers on the IDX" wire item and the suspension notice — both report the move, neither
explains it. Once Fase 4 lands, this card should read **BERGERAK TANPA PENJELASAN**.
