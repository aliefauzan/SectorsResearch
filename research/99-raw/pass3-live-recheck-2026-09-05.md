# Pass-3 live re-check — 5 September 2026

Captured through the in-app browser and public HTTP. No authentication was performed, no
form was submitted, no team was registered, and **no call was made to any `/v2/*` endpoint
on `api.sectors.app`**.

---

## hackathon.sectors.app/matching — recount, 5 September 2026

The board is live and mutable, so these figures move. Counted twice: once from the rendered
page text, once from the DOM (`Sign in to request to join` cards inside the teams section
only, excluding the intro line and the participant-profiles section).

| | 4 Sep capture (`hack-matching.md`) | 5 Sep live |
| --- | --- | --- |
| Public team cards | 44 | **48** |
| Track 01 — AI Agents & Assistants | 16 | **15** |
| Track 02 — Automation & Workflows | 4 | **7** |
| Track 03 — Market Intelligence | 11 | **12** |
| No track preference yet | 13 | **14** |
| Participant profiles | 2 | 2 |

DOM verification, verbatim result:

> `{"team_cards":48,"byTrack":{"1":15,"2":7,"3":12},"noTrackPref":14,"sum":48}`

Track 02 is still the least crowded, but it is no longer "a quarter of Track 01" — it is
roughly half. Four teams joined the board in one day and three of them chose Track 02.

New team names present on 5 Sep and absent from the 4 Sep capture include `Rajdoll`,
`Ritel Unyu`, `vector & velocity`, `flametopus`.

---

## hackathon.sectors.app path probe (fetch, status only)

`/tracks/ai-agents-assistants`, `/tracks/automation-workflows`,
`/tracks/market-intelligence`, `/portal`, `/portal/team`, `/portal/submit`, `/robots.txt`
return **200**.

404: `/rules/id`, `/id`, `/id/rules`, `/bahasa`, `/rules.id`, `/faq`, `/prizes`, `/judges`,
`/timeline`, `/sponsors`, `/tracks`, `/tracks/01`, `/schedule`, `/mentors`, `/resources`,
`/api`, `/sitemap.xml`, `/llms.txt`.

**The Bahasa Indonesia rules remain unpublished as a public route**, despite the rules page
stating "These rules are also available in Bahasa Indonesia". Five candidate routes tested.

`/robots.txt` exists (not previously captured) and carries a Content-Signal preamble
governing `search` / `ai-input` collection.

## The portal gate string, verified

`GET /portal/team` HTML contains, verbatim:

> "Checking your Sectors Account…"

This closes a provenance gap: the 4 Sep `hackathon-home.md` capture contains only
"Checking your Browser…", which is Vercel's checkpoint, a different string.

## Rules page — unchanged since capture

Re-read in full. Dates, eligibility, team sizes (2–4, solo = team of one), the 1,000-credit
grant, the 90-day public-repo requirement, the 1-minute teaser and 3-minute judging video,
the 40/30/30 weights, the IDR 50M / 30M cash / 20M credits split, the trade-execution ban
and the no-financial-advice rule all match `hack-rules.md` word for word.

---

## Host enumeration — certificate transparency, not the sitemap

`https://crt.sh/?q=%25.sectors.app&output=json` returns **9 distinct names**:

| Host | Status | In the dossier before pass 3? |
| --- | --- | --- |
| `sectors.app` | 200 | yes |
| `www.sectors.app` | serves the main app | not named |
| `docs.sectors.app` | 200 | yes |
| `api.sectors.app` | the API | yes |
| `hackathon.sectors.app` | 200 | yes |
| `mining.sectors.app` | 200 | yes |
| `reits.sectors.app` | 200 | yes |
| **`admin.sectors.app`** | **200 — "Sectors Admin", staff email/password login at `#/login`** | **no** |
| **`insider.sectors.app`** | **redirects to `mining.sectors.app`** | **no** |

`insider.` is the pre-2026-01-09 hostname for the mining product, matching the changelog
entry "Adjusted all mining related endpoints to use `/mining` instead of `/insider`".

`admin.` is an internal staff console. No authentication was attempted. There is nothing
participant-facing behind it, but the dossier's previous claim that **five** hosts had been
"enumerated exhaustively" was reached by opening footer links, and footer links do not list
either of these. Certificate transparency does.

## sectors.app footer sweep — re-run

71 distinct internal paths link from the homepage. Every one is already captured or
classified in the dossier. External destinations are exactly:
`instagram.com/sectorsapp`, `linkedin.com/company/sectorsapp/`, `discord.gg/TAnZMmNS4X`,
`mailto:help@sectors.app`, `docs.sectors.app`, `mining.sectors.app`, `reits.sectors.app`,
`supertype.ai`. No further subdomain is linked from the product.

---

## Sources the dossier had never captured

### 1. The public Postman collection

`https://github.com/supertypeai/sectors_api_docs/blob/main/recipes/postman-collection/json/Sectors_API.postman_collection.json`
(raw: `raw.githubusercontent.com/supertypeai/sectors_api_docs/main/...`), 451 KB, schema
`collection v2.1.0`, name "Sectors API".

Diffed against `schema.json`: **70 endpoints in both, zero paths in one and not the other,
and zero query-parameter differences across all 70.** This is independent corroboration of
`02-endpoint-reference.md` and `06-parameter-cheatsheet.md` from a source the dossier had
never opened.

Its collection description carries a **billing table** — a second primary source for the
credit rules, verbatim:

> | Response | Consumes credits? |
> | **2xx** (success) | Yes — the endpoint's stated cost (most cost 1; multi-section reports, multi-classification rankings, and some feeds cost more, as noted on each endpoint). |
> | **404** (addressed resource not found) | Yes — 1 credit. Your request was well-formed and we ran the lookup, but the specific resource you addressed doesn't exist (e.g. an unknown `symbol`/`slug`). You are billed for the lookup, not the result. |
> | **400** (bad request) | No — free. Malformed input (missing/invalid parameters, unknown sections, bad date formats, invalid slugs) is rejected before any lookup runs. |
> | **401 / 403** (auth) | No — free. |
> | **429** (rate limit / quota exhausted) | No — free. |
> | **5xx** (server error) | No — free. A failure on our side is never billed. |

And, on empty results:

> "**List and filter endpoints return `200` with an empty result when nothing matches** — an
> empty collection is a valid answer, not an error. […] These still consume credits (the
> query ran). A `404` is reserved for when the **specific resource you addressed** (a
> `symbol`, `slug`, `index_code`, etc.) does not exist at all."

> "**One exception:** the Company Screener endpoints charge **1 credit on a `400`** *only*
> when using the natural-language `?q=` parameter and the failure occurs after the query has
> been sent to the language model (e.g. an untranslatable query). This recovers the model
> cost already incurred. A `400` from a structured (`where` / `order_by`) query, or any
> validation failure before the model runs, is free. A successful `?q=` screen costs 3
> credits; a successful structured screen costs 1."

### 2. The GitHub organisation `supertypeai`

`https://api.github.com/orgs/supertypeai/repos` — **74 public repositories**. The dossier had
captured only `sectors-agent-skills`. Relevant ones:

| Repo | What it is |
| --- | --- |
| `sectors-mcp` | **The MCP server source.** `src/tools/generated/*.ts` — one file per tool. |
| `sectors_api_docs` | The docs site source, and where the Postman collection lives |
| `sectors_indices_company_list` | A constituent CSV per index — 15 index codes |
| `sectors-kb` | Sectors knowledge base |
| `sectors-agent-skills` | Already captured |
| `sectors_chrome_extension`, `sectors_excel_addin` | Client surfaces with no API docs |
| `coalresearch` | Data behind `mining.sectors.app` |
| `singapore_reits_pipeline` | Data behind `reits.sectors.app` |
| ~40 further `sectors_*` pipelines | `sectors_idx_filing_pipeline`, `sectors_corporate_actions`, `sectors_idx_suspension`, `sectors_dividend_checker`, `sectors_stock_split_checker`, `sectors_get_closed_ipo`, `sectors_idx_daily_data`, `sectors_sgx_short_sell`, `sectors_us_insider_trading`, … — the ingestion code behind individual API datasets |

Most are pushed daily; the org is actively maintained.

### 3. MCP tool count, from the implementation

`sectors-mcp/src/tools/generated/` contains **66 tool files**. The documentation's own
catalogue lists **65** — every `fetch-*` tool. The 66th is **`get-subsectors`**, the only
tool not named `fetch-*`, and it appears in no documentation page.

### 4. `status.supertype.ai`

Referenced twice in the OAuth-connector docs as the place to check when authorization fails.
The host did not resolve from here (`curl` exit before any HTTP status), so it is either
internal, DNS-restricted, or not currently provisioned. Recorded as referenced-but-unreachable.

### 5. Index codes, corroborated three ways

`schema.json` → `/v2/index-daily/{index_code}/` → `<Accordion title="Available index codes">`:

> `ftse`, `idx30`, `idxbumn20`, `idxesgl`, `idxg30`, `idxhidiv20`, `idxq30`, `idxv30`, `ihsg`, `jii70`, `kompas100`, `lq45`, `sminfra18`, `srikehati`, `sti`, `economic30`, `idxvesta28`

17 codes. `sectors_indices_company_list` publishes a CSV for 15 of them (all but `ihsg` and
`sti`). The product's `/indonesia/index/<code>` pages cover 8. The dossier previously listed
8 confirmed plus 5 "plausible candidates" and called the set undocumented.

---

## mining.sectors.app — the `/learn` guides, enumerated

`mining.sectors.app/sitemap.xml` returns **445 URLs** (matching the dossier), of which
**17 are under `/learn`**: one index page (`/indonesia/coal-mining/learn`, title
"Learn About Coal Mining") and **16 articles**, four per commodity.

Titles read from each page's `<title>`:

| Commodity | Background | Quality / types | Price & royalty | Glossary |
| --- | --- | --- | --- | --- |
| Coal | Coal Mining in Indonesia Background | Types of Coal | HBA Coal Prices and Royalties | Coal Mining Glossary |
| Gold | (`1-gold-mining-in-indonesia`) | Gold Quality & Grading | LBMA Gold Prices | (`glossary`) |
| Nickel | (`1-nickel-mining-in-indonesia`) | Types of Nickel | Nickel Prices and Royalties | (`glossary`) |
| Copper | (`1-copper-mining-in-indonesia`) | Copper Quality & Grading | Copper Prices and Royalties | (`glossary`) |

The dossier previously quoted four coal guide titles — "Coal Mining in Indonesia",
"Coal Types and Quality", "HBA Coal Price & Royalty" and "Coal Resources and Reserves" —
in quotation marks with no saved provenance. Three were approximations of the real titles and
**"Coal Resources and Reserves" is not a page at all**: `/coal-mining/learn/` has exactly four
entries and no resources-and-reserves guide. (Resources and reserves live on
`/indonesia/insights/resources-and-reserves`, a different section.) Corrected in
`13-subdomains-and-terms.md`.
