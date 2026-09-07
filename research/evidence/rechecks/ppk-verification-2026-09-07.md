# Verification · Papan Pemantauan Khusus early-warning idea

Date: 7 September 2026. Tooling: agent-reach — Exa web search, `gh-burner.sh` (GitHub burner
account), Jina Reader, direct `curl`.

**Reddit and Twitter/X were not reachable this session.** The OpenCLI browser bridge is not
connected (`BROWSER_CONNECT`), `rdt-cli` is not installed, and `twitter-cli` returned
`HTTP 404` with a failed ClientTransaction init. So no social-sentiment sampling was done —
the real-world-problem evidence below rests on news coverage, exchange announcements and
GitHub, not on forum discussion.

## The problem is real and documented

| Claim | Evidence |
| --- | --- |
| Retail investors publicly protested the Full Call Auction regime on the special monitoring board — protest flower wreaths sent to the IDX building in SCBD | [Kompas, 4 Jun 2024](https://money.kompas.com/read/2024/06/04/090900826/investor-ritel-tolak-papan-pemantauan-khusus-fca-ini-respons-bei) · [Liputan6, 13 Jun 2024](https://www.liputan6.com/saham/read/5619493/heboh-full-call-auction-atau-fca-investor-saham-ritel-merasa-dirugikan) |
| FCA rolled out in two stages: hybrid 12 Jun 2023, full FCA 25 Mar 2024 | Kompas, quoting IDX's I Gede Nyoman Yetna |
| **172 stocks were on the board as of Jan 2026**; 16 entered in the fortnight 2–15 Jan 2026 alone, several exiting within days | [EmitenNews, 18 Jan 2026](https://www.emitennews.com/news/16-saham-jadi-anggota-baru-efek-papan-pemantauan-khusus-ini-datanya) |
| Membership is announced per period with entry date, exit date and criterion numbers — retrospectively | same |

## The 11 criteria, current version

Source: IDX announcement **Peng-UK-00035/BEI.PLP/08-2026**, effective **5 August 2026**,
[mirrored by BCA Sekuritas](https://bcasekuritas.co.id/api/pdf/Pemantauan%20Khusus%20-%20Perubahan%20-%205%20Agustus%202026.pdf).
Governing rule is Peraturan Nomor II-X; free-float requirements come from I-A and I-V.

1. Average price < Rp51 **and** low liquidity (avg daily value < Rp5,000,000 and avg daily volume < 10,000, over the last 3 months)
2. Latest audited financials carry a **disclaimer** opinion
3. No revenue, or no change in revenue versus the previous financial statements
4. Mineral/coal miner (or parent of one) past production stage but not yet at sales stage by the end of its 4th book year since listing, with no core-business revenue
5. **Negative equity** in the latest financial report
6. Fails the free-float requirements of I-A / I-V
7. Low liquidity standalone (same thresholds as criterion 1's second half)
8. Company under PKPU, bankruptcy, or annulment of a composition agreement
9. A materially contributing subsidiary in that condition
10. Trading suspended for **more than 1 exchange day** due to trading activity
11. Other conditions set by the Exchange with OJK approval

## Sectors covers none of it, but can compute most of it

`grep -i` over `evidence/spec/schema.json` (929 KB) and `evidence/spec/llms-full.txt` (840 KB)
for `pemantauan`, `special monitoring`, `notasi khusus`, `call auction` → **zero matches**.
Control greps for `listing_board`, `Acceleration` and `Main board` all hit, so the search is
sound. `listing_board` carries only Main / Development / Acceleration.

Mapping the criteria onto data Sectors does expose:

| # | Computable | Source |
| --- | --- | --- |
| 1 | ✅ | `last_close_price` (screener) + `/v2/daily/{symbol}/` — 90-day window is exactly the 3-month test |
| 2 | ❌ | audit opinion is nowhere in the API |
| 3 | ✅ | `total_revenue_mrq`, `revenue[YYYY]`, `/v2/financials/quarterly/{symbol}/` |
| 4 | ⚠️ partial | `/v2/mining/companies/performance/{slug}/` → `mining_operation_status`, `production_volume`, `sales_volume`, plus `listing_date`. Only 9 mining companies have detail records |
| 5 | ✅ | `total_equity_mrq` — one screener call for the whole market |
| 6 | ✅ | `/v2/free-float/`, 1 credit per 100 companies |
| 7 | ✅ | `/v2/daily/{symbol}/` |
| 8 | ⚠️ partial | `/v2/news/` + `/v2/filings/` free text; `/v2/tags/` carries `violation`, `ojk`, `delisting` |
| 9 | ⚠️ partial | same, harder — needs the subsidiary link |
| 10 | ✅ | `/v2/suspensions/` — `symbol`, `suspension_date`, `reason`, refreshed daily 10:00 WIB |
| 11 | ❌ | discretionary |

**7 of 11 computable, 3 partial, 2 out of reach.**

Confirmed against the recorded payload `harness/recorded/v2_tags.json`, which contains
`delisting`, `free-float-compliance`, `free-float-requirement`, `suspension`, `trading-halt`,
`violation`, `rights-issue`, `hmetd` — and `harness/recorded/v2_suspensions.json`, whose rows
carry Indonesian free-text reasons such as *"peningkatan harga kumulatif yang signifikan …
dalam rangka cooling down sebagai bentuk perlindungan bagi investor"*.

## Prior art — what already exists

**Displaying the current list is taken.** Stockbit ships a Pemantauan Khusus catalog page
in-app ([Stockbit Snips, 2 Nov 2024](https://snips.stockbit.com/investasi/apa-itu-papan-pemantauan-khusus-bei)),
and IDX publishes the official list at `/id/perusahaan-tercatat/daftar-efek-pemantauan-khusus/`
plus notations at `/id/perusahaan-tercatat/notasi-khusus/`. Both are retrospective.

**GitHub.** Searches for `papan pemantauan khusus`, `pemantauan khusus saham`,
`IDX notasi khusus`, `IDX full call auction FCA`, `notasi khusus`, `delisting risk indonesia
stock` returned **zero repositories**. Code search for `pemantauan_khusus` returned two:

- **`prayogiii/quant-engine`** — a Streamlit tool with a **hardcoded, hand-pasted PPK ticker
  list** used purely as an exclusion filter. Treats the board as a blacklist to avoid. No
  prediction. Supporting evidence, not competition: builders maintain this list manually.
- **`cuthbertyoungg/FINSCORE`** — the real prior. A deployed FastAPI service (LightGBM + Cox
  survival + SHAP, ~3,200 parquet files) scoring **financial distress** of IDX companies from
  annual statements, using delisting and pemantauan as distress *labels*. Created 15 Jul 2026,
  0 stars. **Built on yfinance, not Sectors.** Different target and horizon — next-year
  distress probability from annual data, versus mechanical criterion proximity on rolling
  3-month liquidity and latest quarterlies. Adjacent enough to name in the video.

**Academic.** Several Indonesian papers apply Altman / Zmijewski / Ohlson to companies
**already on** the board, and one builds a delisting early-warning SVM for sharia stocks.
All take PPK membership as the *sample*; none predict *entry into* it.

**No product, repo or paper found that answers "which stocks are about to enter".**

## Engineering findings from the live checks

- **`www.idx.co.id` is behind Cloudflare and returns 403 even with a browser User-Agent** —
  both the `umbraco/Surface/ListedCompany/GetStockList` endpoint and static announcement PDFs.
  So the `pdf_url` field in `/v2/suspensions/` rows is **not directly fetchable**.
- The **BCA Sekuritas mirror serves the same announcements fine** (HTTP 200,
  `application/pdf`). That is the reachable path to official PPK announcements for
  ground-truth labels.

## Matching board, recounted 7 September 2026

46 public teams: **15 Track 01 · 7 Track 02 · 11 Track 03 · 13 undecided**. Down from 48 on
5 Sep (the board is mutable in both directions). Track 02 still the least crowded at 7.

No visible team mentions the special monitoring board, delisting, suspensions, mining, or
licences. Only 7 cards carry descriptive text, and most are recruiting notes — so this is weak
evidence of absence, not proof.
