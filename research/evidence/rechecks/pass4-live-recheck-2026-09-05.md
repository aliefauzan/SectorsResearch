# Pass 4 — live re-check evidence, 5 September 2026

Verbatim captures backing the corrections in
[`audit/VERIFICATION-PASS-4.md`](../../audit/VERIFICATION-PASS-4.md). No `/v2/*` call was made to
`api.sectors.app`; that host was excluded from every probe. No account was created, no form
submitted, no team registered, no credential entered.

---

## 1. Documentation drift since capture — none

Re-fetched and hashed against the committed copies:

```
docs.sectors.app/schema.json     200  951210 bytes  md5 4c07abd19af67c726a97478bc4dca26f  IDENTICAL
docs.sectors.app/llms.txt        200   32677 bytes  md5 453137d8445ef97991d6048189baf559  IDENTICAL
docs.sectors.app/llms-full.txt   200  839575 bytes  md5 889b0d411f4a5231468247e37146b7b3  IDENTICAL
```

`sectors.app/release` — latest entry is still **2026-08-10, "Foreign Flows"**. Nothing added
since the 4 September capture.

---

## 2. Matching board — live recount, 5 September 2026

Counted three independent ways inside the "Public teams" section only (from the
`FILTER TEAMS` heading to the `FILTER PROFILES` heading, so the participant-profile cards
below cannot leak in — the error pass 1 made):

```
team cards by "Sign in to request to join" button : 48
team cards by "N/4 participant(s)" string          : 48
team cards by name extraction after TRACK label    : 48

byTrack {"01":15, "02":7, "03":12, "—":14}
size distribution {1: 45, 2: 2, 3: 1}   participants on board: 52   cards at 4/4: 0
```

Identical to the pass-3 count taken earlier the same day. The board header reads
"Teams with room to grow", so full teams are excluded by construction.

**Descriptions (new — pass 3 recounted the numbers but did not re-read the text).**
22 of the 48 cards carry text. Four disclose a project:

| Team | Track | Verbatim |
| --- | --- | --- |
| Xninetzy | 03 | "Solo builder. Not currently looking for additional teammates. Building SAKTI end-to-end across AI/agentic systems, backend infrast…" |
| Apriyanto | 03 | "Hiddwn gems & early accumulation by bandar" |
| RWL | 02 | "daily watch of stock with certain filter (RSI/MA/MACD)" |
| vector & velocity | 03 | "Vector & Velocity represents the strategic synergy between a human Navigator and an Artificial Intelligence Driver…" |

Two teams now recruit video/motion skill, where on 4 September none did:

| Team | Track | Verbatim |
| --- | --- | --- |
| Sepi | 02 | "Cari 1 orang video/motion untuk judging video 3 menit. Produk sudah didefinisikan dan backend dikerjakan solo. Yang dibutuhkan: na…" |
| StockPro | 03 | "Need a designer, editor, motion graphics and maybe someone who familiar with cron ,automations ,n8n and hermes" |

---

## 3. Rules page — unchanged since capture

Method: extracted every sentence of ≥40 characters from the live page, normalised dashes,
quotes and markdown, hashed each, and diffed the hash set against the same extraction from
`hack-rules.md`.

```
capture sentences: 111    live sentences: 108    capture-only after normalisation: 7
```

All 7 are markdown-table-versus-innerText line-joining artefacts, e.g. the capture's
`Registration closes 22 September 2026, 23:59 WIB` is two lines in the rendered page. No
content difference. Spot-checked verbatim and present in both: `ask+hackathon@incoming.supertype.ai`,
`Organizers may update these rules before 19 August 2026`, `also available in Bahasa Indonesia`,
`solo or in teams of 2–4 participants`, `1,000 Sectors API credits`, `IDR 50,000,000`,
`at least 90 days after winners are announced`, the leaked-key freeze exception, and `SARA`.

---

## 4. Bahasa Indonesia rules — definitively not published on the site

The rules page states: *"These rules are also available in Bahasa Indonesia; submissions and
videos are accepted in Bahasa Indonesia or English."* Four independent checks say the site
does not carry them:

1. **Twenty candidate routes, all 404** (fetched from inside the origin):
   `/rules/id`, `/id/rules`, `/rules-id`, `/rules.id`, `/aturan`, `/peraturan`, `/id`,
   `/in/rules`, `/rules/bahasa`, `/rules/indonesia`, `/rules-bahasa`, `/id/aturan`,
   `/ketentuan`, `/syarat`, `/rules/in`, `/docs/rules-id`, `/rules_id`, `/aturan-resmi`,
   `/peraturan-resmi`, `/tracks/` (the last is 404 as a bare path).
2. **The client bundle knows only five routes.** Scanning all 25 loaded scripts for path
   literals returns exactly `/matching`, `/portal`, `/portal/team`, `/rules`, `/tracks/`.
   There is no Indonesian route to reach.
3. **`?lang=id` and `Accept-Language: id-ID` are both ignored** — all three fetches return the
   same 130,787-byte English document containing "Official rules" and "Spirit of the
   competition" and no Indonesian headings.
4. **No i18n signals in the markup**: `<html lang="en">`, zero `<link hreflang>` elements,
   zero links whose href mentions `id`, `bahasa`, `indonesia` or `lang`.

`/sitemap.xml` is 404; `/robots.txt` is 200.

---

## 5. `status.supertype.ai` — does not exist

Referenced twice in the OAuth-connector docs. Pass 3 recorded it as "did not resolve from
here". It is not a network condition:

```
dig @8.8.8.8 status.supertype.ai  ->  status: NXDOMAIN
dig @1.1.1.1 status.supertype.ai  ->  status: NXDOMAIN
curl https://status.supertype.ai/ ->  curl 000 (no resolution)
supertype.ai itself                ->  200, resolves to 172.67.187.234 / 104.21.48.199
```

It also appears in **none** of the 22 names in `supertype.ai`'s certificate-transparency
record (crt.sh): `*.`, `brillian.`, `charta.`, `coffee.`, `collective.`, `coursebook.`,
`datasheets.`, `fellowship.`, `hq.`, `kipas.`, `kipasdb.`, `mailroom.`, `pages.`, `s.`,
`sectors-mcp.`, `sectors.`, `segments.`, `summary.`, `superlative.`, `umai.`, `www.`, apex.

Two of those are worth noting because the dossier's host enumeration only ever covered
`*.sectors.app`: **`sectors-mcp.supertype.ai`** (already documented as the MCP endpoint) and
**`sectors.supertype.ai`**.

---

## 6. Host enumeration — two CT sources agree, and DNS brute force is worthless here

**crt.sh** (`?q=%.sectors.app`) and **certspotter**
(`api.certspotter.com/v1/issuances?domain=sectors.app&include_subdomains=true`) independently
return the identical set of **10 names**:

```
*.sectors.app  admin.sectors.app  api.sectors.app  docs.sectors.app  hackathon.sectors.app
insider.sectors.app  mining.sectors.app  reits.sectors.app  sectors.app  www.sectors.app
```

**The third method returns nothing, and that is itself the finding.** A 103-word DNS
brute-force (excluding `api.`) got 103 hits — because `*.sectors.app` is **wildcard DNS**:

```
definitely-not-real-1234.sectors.app  ->  216.150.1.65  216.150.16.129
```

Every label resolves to the same pair of Vercel edge IPs, and HTTPS to them fails, so DNS
enumeration cannot distinguish a real host from a typo. The corollary matters for the closure
argument: because the certificate is a **wildcard**, CT can only prove that a name was
*separately* certificated — it cannot prove no other host exists behind the wildcard.

---

## 7. `sectors-mcp`'s own `schema.json` versus the committed one

`raw.githubusercontent.com/supertypeai/sectors-mcp/main/schema.json`, 945,791 bytes
(the committed copy from `docs.sectors.app` is 951,210).

```
paths: 70 in both            paths unique to either: 0
parameter names:  0 differences across all 70 endpoints
parameter schemas: 0 differences (enums, defaults, min/max)
credit-cost sentences: 0 differences
"Default behavior (…) consumes N credits": 0 differences
200-example response shapes: 0 differences
securitySchemes: identical
screener field sets: IDX 219 = 219, SGX 85 = 85, zero symmetric difference
index-daily "Available index codes" accordion: byte-identical (all 17)
```

46 endpoints differ in prose only. Representative diff, `/v2/sgx/companies/top/`:

```
- <Note>Get valid sector slugs from the [SGX Sectors](https://docs.sectors.app/api-references/v2/singapore/helper-list/sgx-sectors) endpoint.</Note>
+ <Note>Get valid sector slugs from the [SGX Sectors](../singapore/sgx-sectors) endpoint.</Note>
```

i.e. relative versus absolute documentation links. This is a **third** independent source
agreeing with the OpenAPI spec and the Postman collection on every structural fact.

---

## 8. `sectors_indices_company_list` — what settles `sti`

`index_name.csv`, the registry the daily scraper joins against — **18 rows**:

```
index_code,index_name,index_code_yf
LQ45,LQ45,^JKLQ45
IDX30,Indeks IDX30,IDX30.JK
IDXHIDIV20,IDX High Dividend 20,IDXHIDIV20.JK
IDXBUMN20,IDX BUMN20,IDXBUMN20.JK
IDXV30,IDX Value30,IDXV30.JK
IDXG30,IDX Growth30,IDXG30.JK
IDXQ30,IDX Quality30,IDXQ30.JK
IDXESGL,IDX ESG Leaders,IDXESGL.JK
KOMPAS100,KOMPAS100,KOMPAS100.JK
SRI-KEHATI,SRI-KEHATI Index,SRI-KEHATI.JK
SMinfra18,SMinfra18,SMINFRA18.JK
JII70,Jakarta Islamic Index 70,JII70.JK
FTSE,FTSE Indonesia Index,WIIDN.FGI
IHSG,IHSG,^JKSE
STI,Straits Times Index,^STI
KLSE,Bursa Malaysia,^KLSE
ECONOMIC30,IDX Cyclical Economy 30,ECONOMIC30.JK
IDXVESTA28,IDX-Infovesta Multi-Factor 28,IDXVESTA28.JK
```

`index_daily_data_scraper.py`:

```python
# Fetch STI, KLSE, FTSE from yf
indices = ["^STI","^KLSE","WIIDN.FGI"]
...
supabase.table("index_daily_data").insert(dict(scrape_daily.iloc[sub_sector])).execute()
```

and the IDX side pulls `https://www.idx.co.id/primary/TradingSummary/GetIndexSummary`,
renaming `COMPOSITE` to `IHSG`. Schedule: `0 11 * * 1-5`, commented *"Run every weekday at
6pm (Western Indonesia Time)"*.

`company_list/` holds **15** constituent CSVs — every code except `IHSG` and `STI`, which is
also the pair the agent-skills docs page omits from its 15-code list
(`llms-full.txt:10629`, `evidence/sectors/agent-skills/SKILL.md:282`).

---

## 9. Ingestion repos — provenance for `11-data-provenance.md`

`github.com/supertypeai` has **74** public repos. READMEs and workflow crons read this pass:

- **`sectors_idx_filing_pipeline`** — "Harvests IDX insider ownership announcements, parses the filings out of their PDFs, repairs what it can, and writes the result to Supabase as filings and news. It runs unattended **every two hours**." Stages: `ingestion → downloader → parser → dedup → generate → insert` into `idx_filings` + `idx_news`.
- **`sectors_news`** — "A news scraping and classification pipeline focused on IDX (Indonesia) and SGX (Singapore) sources. The system scrapes articles, summarizes and classifies them with LLMs, scores and tags them, and posts results to Supabase." Workflows `pipeline_idx.yaml` / `pipeline_sgx.yaml`, cron `15 */4 * * *`.
- **`sectors_corporate_actions`** — "Scraper pipeline for all corporate actions in IDX using data from [new.sahamidx.com]… there are several unavailable corporate action data in that source that we need to manually scrape it. The list of manually scraped data right now are 1. Right Issue… 2. Reverse Stock Split… 3. Buybacks… we need to manually add it using [this streamlit app](https://sectors-corporateaction.streamlit.app)".
- **`sectors_dividend_checker`** — "automated scripts… executed by GitHub Actions to scrape data from specified websites… all data is sourced from sahamidx.com".
- **`sectors_idx_suspension`** — workflow `idx_suspension_ci.yaml`, cron `0 3 * * *`.
- **`sectors_idx_daily_data`** — "Fetch idx_daily_data data such as close price, volume, foreign transaction volume per company everyday".
- **`sectors_get_closed_ipo`** — "will get the all the symbol from company with null ipo price in the database, then retrieve the data in page 1 of e-ipo closed ipo page and update the null data in database".
- **`coalresearch`** — `commodity_price`: "Monthly price history per commodity. Source: non-gold/silver: … scrapes from [ESDM Minerba](https://www.minerba.esdm.go.id/harga_acuan). Running on weekly basis and will automatically sync to `db.sqlite`; gold & silver: … [LBMA]".
- **`singapore_reits_pipeline`** — "Groundwork for the Singapore REITs feature on sectors.app… 39 trusts, FY2023–FY2025… ~101 of 117 PDFs… locked 6-table schema". Parsing engine switched from LlamaParse to Datalab.
- **`sectors_guard` / `sectors_guard_validator`** — "A comprehensive data validation dashboard with automated anomaly detection and email notifications… monitors data quality across multiple tables in Supabase."
- **`sectors_chrome_extension`** — "Sectors Ticker Lens (v1.1.3)… surfaces real-time financial data, valuation metrics, insider trading filings, and natural language AI screening when you hover over stock symbols on any webpage." Confirms the IDX report section names and the four SGX ones.
- **`sectors-kb`** — recipes and a link to a "Sectors Glossary" wiki. **The wiki is empty**: a single "Welcome to the sectors-kb wiki!" page, one revision, last edited 17 October 2023. The repo itself is v1-era (animated plots in R, a SectorScan Streamlit tutorial). It does **not** close the "internal data dictionary" gap.
- **`sectors_excel_addin`** — README is one line (the repo name). No documentation.

Repos in the org that no prior pass listed and that suggest surfaces the dossier does not
cover: `sectors_us_insider_trading`, `sectors_us_cron`, `us-sectors-kb` (a US-market
surface), `sectors_idx_fear_and_greed_index`, `sectors_get_esg_score`,
`sectors_price_anomaly_updater`, `sectors_generate_subsector_index`,
`sectors_get_market_cap_worldwide_data`, `summarize-agm-result`, `sectors_ticker_pdf_generator`,
`sectors_dcf_calculation`, `sectors_forecast_growth_rate`, `broksum`, `buyback_notify`,
`run_sectors_watchlist_notification`.

---

## 10. Discord and Slack — read-only metadata, neither joined

**Discord `discord.gg/TAnZMmNS4X`** — invite metadata read from the public invite API without
authenticating or joining:

```
guild            : Supertype   (id 1110875765492428861)
description      : "Supertype is the makers of Sectors Financial Data Suite and an
                    industry-leading AI consultant / product incubator."
members          : 1346        online: 80
landing channel  : 👋・welcome
invite expires   : never
features         : MEMBER_VERIFICATION_GATE_ENABLED, COMMUNITY, GUILD_ONBOARDING, …
```

It is the **general Supertype community server**, not a hackathon channel, and it carries a
member-verification gate. Content is unreadable without an account → **closed**.

**Slack `join.slack.com/t/sectorshackathon/…`** — the invite landing page renders without
signing in:

```
"Accept Aurellia Christie's invitation to Sectors Hackathon"
"See what Aurellia Christie and 104 other members are doing in Sectors Hackathon."
"No setup required. This invitation expires in 15 days."
```

So: workspace name **Sectors Hackathon**, **105 members**, and the shared invite link
**expires around 20 September 2026 — two days before registration closes**. Reading the
channels requires creating an account → **closed**.

---

## 11. Wildcard-DNS raw evidence

```
$ dig +short definitely-not-real-1234.sectors.app
216.150.1.65
216.150.16.129
$ curl -o /dev/null -w '%{http_code}' https://zzqx7k9nonexistent.sectors.app/
000
```
