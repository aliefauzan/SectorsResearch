# Problem Research · The IDX Suspension-to-Delisting Ladder

Research only, 7 September 2026. No solution proposed here — the point is to establish
whether a real problem exists, who it hurts, and whether Sectors can see it.

Tooling: agent-reach — Exa search, `gh-burner.sh`, Jina Reader, direct `curl`.
**Reddit and Twitter/X were unreachable** (OpenCLI bridge not connected, `twitter-cli` HTTP 404),
so nothing below rests on forum sentiment.

---

## The rule is a clock, and the clock is public

**Peraturan BEI Nomor I-N**, in force since 6 May 2024, replaced the old I-I and I.A.7. It
turns suspension into a fixed escalation ladder, and every step is measured in months from
the suspension date:

| Months suspended | What IDX does |
| --- | --- |
| 3 | Company must publicly disclose a recovery plan, then report progress every 6 months |
| 6 | **IDX publicly announces potential delisting** |
| 6 → 24 | IDX repeats that announcement **four times**, with a hearing of directors, commissioners and founders at each step |
| **24** | Suspension in regular, cash, or all markets for **at least 24 months** is grounds for forced delisting |
| decision + 1 month | Company must disclose a share-buyback plan (POJK 3/2021, SEOJK 13/2023) |
| decision + up to 6 months | **Buyback must be executed** — this is the holder's only exit |
| buyback disclosure + 6 months | Delisting takes effect |

Forced delisting also triggers on bankruptcy, on failing listing requirements including free
float, and on legal issues with no adequate recovery.

Everything after the suspension date is arithmetic. No forecasting is required to know when a
given stock reaches any rung.

---

## The live numbers

**Announcement Peng-S-00019/BEI.PLP/06-2026, as at 30 June 2026: 59 issuers flagged as
potential forced delisting** for being suspended more than six months. IDX publishes the
months-suspended figure per ticker.

The range is 7 to 87 months:

| Months | Tickers |
| --- | --- |
| 87 / 86 / 84 | KBRI · BTEL · TRIO |
| 80 / 78 / 77 / 76 | ARMY · SMRU, TRAM · HOME, RIMO · SIMA |
| 72 / 70 / 67 | POOL · NUSA · POSA |
| 47 / 46 | MAGP · JSKY, PURE, HOTL |
| 40 / 37–38 | CBMF · **WSKT** |
| 35 / 34 | CPRI, GAMA, HKMU · TECH |
| 28 / 26 | BOSS, DEAL, ETWA, IIKP · KAYU |
| **23** | ARTI, BIKA, **INAF**, MKNT, POLL — one month from the 24-month trigger |
| 21 / 20 | IPPE · ALMI |
| 17 | LMSH, MFMI, MTSM, **PLIN**, WICO, **SMCB**, **FASW** |
| 16 | **WIKA**, BEBS |
| 13 / 12 | TGUK, ALTO · PMMP, PTMR, SWAT, TGRA, ZBRA |
| 11 / 10 / 8 / 7 | KIAS · FIMP · DPNS, GLOB, MENN · BIMA, MTPS, TOPS |

Two things stand out.

**These are not all penny stocks.** WIKA and WSKT are state-owned construction companies.
PLIN is Plaza Indonesia Realty, SMCB is Solusi Bangun Indonesia, FASW is Fajar Surya Wisesa,
INAF is Indofarma.

**The next crossings are computable today.** The five at 23 months crossed 24 in July 2026.
IPPE at 21 crosses around September 2026, ALMI at 20 around October. The block at 17 months
crosses around January 2027. **WIKA at 16 months crosses around February 2027.**

> One inconsistency to resolve before using this: the source article reports WSKT as 38 months
> in one paragraph and 37 in another. Take the figure from the IDX announcement itself.

## What already happened, and who it hurt

Separately, **18 issuers are scheduled for delisting effective 10 November 2026**, announced
10 April 2026. Seven for bankruptcy — COWL, MTRA, **SRIL**, TOYS, SBAT, TDPM, TELE — and
eleven for suspension beyond 50 months, including LCGP, SUGI, MABA, LMAS, SKYB.

- **Lo Kheng Hong**, the best-known retail investor in Indonesia, has an estimated
  **Rp30,56 miliar** locked in SRIL.
- **Pension funds and mutual funds are among the trapped holders.**
- Some of these are majority public-owned: **LCGP 87,38%**, **DUCK 86,9%**.
- IDX required a buyback between **11 May and 9 November 2026** — the only exit, and it closes
  the day before delisting.

Katadata's headline on it: *"Investor Ritel di Pusaran Delisting: Rugi dan Terjebak Tanpa
Perlindungan."*

The 10 November 2026 date falls **after** the 30 September submission deadline, so this is an
unresolved, running story throughout judging.

---

## Can Sectors see it?

**`/v2/suspensions/` is a full historical archive.** The recorded payload reports
`total_count: 583`, paginated at max 30 per page, filterable by `symbol`, and both `start` and
`end` are optional with no lower bound. **The entire IDX suspension history costs roughly 20
credits.**

Rows carry `symbol`, `suspension_date`, `reason` (Indonesian free text) and `pdf_url`.

### The gap that matters

**There is no lift date and no status field.** Confirmed against the recorded payload — the
only keys are the four above. So "months *continuously* suspended", the exact quantity the
rule turns on, is **not directly computable** from this endpoint.

It is *inferable*: a suspended stock returns a well-formed all-zero row from `/v2/daily/`
rather than an error (documented in `docs/api/10-domain-pitfalls.md`). So suspension start
plus continuing all-zero daily rows establishes that the suspension still runs. That inference
needs verifying against a known case before anything is built on it.

Supporting data that is available: `/v2/tags/` carries `delisting`, `suspension`,
`trading-halt`, `free-float-compliance`, `free-float-requirement` and `violation`, so
`/v2/news/` and `/v2/filings/` can be filtered for the bankruptcy and free-float limbs of the
rule. `/v2/free-float/` costs 1 credit per 100 companies.

**Sectors carries no delisting or suspension-status field of its own** — `grep` over
`schema.json` and `llms-full.txt` finds no `pemantauan`, `special monitoring`, `notasi khusus`
or `call auction` either, so the whole IDX administrative ladder is invisible in the API.

---

## Prior art

**GitHub: zero repositories** for `IDX delisting tracker`, `suspension tracker stock
indonesia`, `BEI suspensi emiten`.

**Media covers each announcement, then stops.** Liputan6, Stockwatch, Suara, Periskop and
Kompas all published the 59-issuer list within days of the IDX announcement. None of them
maintains a running clock, and the coverage disappears until the next announcement six months
later.

**IDX publishes the months-suspended figure only inside a PDF announcement, twice a year per
issuer.** `www.idx.co.id` returns **403 behind Cloudflare even with a browser User-Agent**,
including static announcement PDFs — so the `pdf_url` on every `/v2/suspensions/` row is not
directly fetchable. Broker mirrors such as BCA Sekuritas serve the same documents at HTTP 200.

Nobody maintains the ladder as a live, per-ticker countdown.

---

## Business filter

| Filter | Verdict |
| --- | --- |
| Who has budget | Pension funds and mutual funds already hold these names and have a fiduciary duty. Securities firms carry the margin and collateral exposure |
| Mandatory action | Yes — the buyback window is a legally mandated, time-boxed exit under POJK 3/2021 |
| Hard deadline | Yes, and it is published per issuer |
| Recurring | Continuously — 59 issuers each advancing one rung per month |
| Loss in rupiah | Total loss on delisting. Rp30,56 miliar in one named retail case alone |
| Model risk | **None.** The ladder is arithmetic on a date |

The last row is the unusual one. Every other candidate in this dossier needs a score, a
threshold or a forecast that could be wrong. This one does not.

---

## What is still unverified

1. Whether continuing all-zero `/v2/daily/` rows reliably indicate an unlifted suspension.
   Test against a known case — WSKT or KBRI — before relying on it.
2. Whether `/v2/suspensions/` records a *lifting* as its own row with a distinguishing
   `reason` string. The 583 records have not been swept; only the most recent 20 are cached.
3. The exact WSKT figure, 37 or 38 months.
4. Whether Stockbit, RTI or any broker app surfaces months-suspended. Their PPK catalog page
   is confirmed; this is not.
5. Whether pension funds are actually blocked from exiting, or merely choose not to. The
   Katadata and beritabisnis reporting asserts they are trapped; the mechanism was not
   confirmed against a primary source.

## Sources

- Peraturan I-N mechanics — Bisnis.com, 7 May 2024, two articles
- 59-issuer list and per-ticker months — Periskop, 31 Aug 2026, citing Peng-S-00019/BEI.PLP/06-2026; corroborated by Liputan6 (21 Jul 2026), Stockwatch (1 Jul 2026), Suara (8 Jul 2026)
- 18-issuer delisting, 10 Nov 2026 — Kompas, 14 Apr 2026; Katadata, 20 Apr 2026; beritabisnis, 21 Apr 2026
- Endpoint shapes — `harness/recorded/v2_suspensions.json`, `v2_tags.json`, and `docs/api/02-endpoint-reference.md`

---

# Second dig, same day · two things the ladder hides

## 1. The bankruptcy branch — the buyback is not guaranteed

The buyback is what makes delisting survivable. It does not always happen.

IDX's own Director of Company Valuation, quoted May 2024: an issuer may be unable to buy back
**because it has been declared bankrupt, or because it has no clear controlling shareholder.**
When the controller cannot perform, the matter escalates to the **Kejaksaan Agung** to
liquidate company assets — a prosecutorial process measured in years.

So the ladder forks, and the fork decides everything for a holder:

| Branch | Outcome |
| --- | --- |
| Controller exists and is solvent | Mandatory buyback under POJK 3/2021 and POJK 29/2023. Holder recovers something at a regulated price |
| **Pailit, or no identifiable controller** | No buyback. Holder waits on asset liquidation via Kejagung |

**Seven of the 18 delisting on 10 November 2026 are in the bankruptcy branch** — COWL, MTRA,
**SRIL**, TOYS, SBAT, TDPM, TELE. Lo Kheng Hong's Rp30,56 miliar is in SRIL, which is why
there is nothing for him to say.

The single most valuable bit of information for anyone holding a suspended stock is therefore
not *"will this delist"* — the ladder already answers that. It is **"which branch am I in."**

And that bit is determinable from Sectors data. The `ownership` section of
`/v2/company/report/{symbol}/` costs 1 credit and returns `major_shareholders`,
`whale_investors` and `conglomerates_group` — enough to establish whether an identifiable
controller exists. Bankruptcy and PKPU surface through `/v2/news/` and `/v2/filings/`, whose
`/v2/tags/` vocabulary includes `violation`, `delisting` and `suspension`.

Sanctions for failing to buy back are administrative, under Articles 93 and 94 of POJK 3/2021.

## 2. The institutional obligation — marking a security that has no price

This is where the money and the deadline are.

**Peraturan IV.C.2** (KEP-367/BL/2012) requires a Manajer Investasi to compute the **Nilai
Pasar Wajar** of every security in a mutual fund portfolio, with an LPHE obliged to supply
fair prices. A suspended stock has no market price, so it must still be marked — by judgment,
against a rule.

The consequences of getting it wrong are specific:

- On discovering a NAV calculation error, the MI must notify the Custodian Bank, copying OJK,
  **by 24:00 WIB the same day**
- A Custodian Bank that discovers it reports to OJK by 24:00 WIB the next working day
- The Custodian Bank must compute per-unit compensation and notify every affected holder
- **Compensation is borne by whichever party caused the error**, paid within **7 exchange days**

So an MI holding a name on the ladder carries a live, dated, personally-borne liability for
mismarking it. That is the institutional payer, the mandatory action and the deadline in one
regulation — and it is triggered by exactly the events this research tracks.

**Unverified:** how MIs currently mark suspended holdings in practice, and whether any of the
59 flagged issuers sit in retail mutual fund portfolios today. Both need a primary source
before the claim is used.

## Sources added

- Buyback failure and Kejagung escalation — Bisnis.com, 10 May 2024
- Buyback obligation and sanctions — Kompas, 15 Mar 2021, quoting IDX on POJK 3/2021 Arts. 93–94, effective 22 Feb 2021; POJK 29/2023
- Fair value and NAV error procedure — OJK Peraturan IV.C.2 (KEP-367/BL/2012) and the SEOJK on NAV calculation error resolution
