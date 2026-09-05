# FLARE, the Community Programs, and How Sectors Engineers Things

> Tenth-pass finding, from opening the remaining footer links individually — the ones a
> sitemap sweep lists but does not read. Several turn out to be directly useful.

---

## 1. FLARE — the missing data dictionary for the banking fields

**FLARE** (Financial Literacy, Research and Education) is Sectors' education initiative,
written by **Samuel Chan** (co-founder of Algorit.ma, Supertype.ai and Sectors; Developer
Advocate and Lead Engineer). It is a three-part series on analyzing bank financials.

| Part | Article | Covers |
| --- | --- | --- |
| 1 | [Earning Assets & Asset Quality](https://sectors.app/finance/asset-quality) | Earning/productive assets, **collectibility classification**, asset quality of securities, government securities and BI certificates, placements, equity participation, credit quality, **NPLs, restructured loans, Loan at Risk (LAR)** |
| 2 | NII, NIM and IRR | Net interest income, net interest margin, interest-rate risk |
| 3 | [Bank Liquidity & Credit Risk](https://sectors.app/finance/bank-liquidity) | **LCR, HQLA, LDR, CASA ratio, CAR** and its formula, Basel III framework |

**Why this matters:** these articles are the definitions behind the API's banking fields.
The screener exposes `casa_ratio`, `loan_to_deposit_ratio`, `liquidity_coverage_ratio`,
`capital_adequacy_ratio`, `high_quality_liquid_asset`, `net_interest_margin`,
`non_performing_loan`, `special_mention_loan`, `restructured_loan_current`,
`core_capital_tier1`, `supplementary_capital_tier2`, `credit_rwa` — and nothing in the API
documentation explains what any of them mean or how they should be interpreted.

FLARE does, with the regulatory citations Sectors standardizes against:

- Bank Indonesia Regulation **7/2/PBI/2005** — Asset Quality Rating for Commercial Banks
- **OJK 40/POJK.03/2019** — Penilaian Kualitas Aset Bank Umum
- **Basel III** — LCR and capital definitions
- OJK Minimum Capital Adequacy Requirement for Commercial Banks

> If your project touches Indonesian banks — and banks are the largest, most liquid, most
> analyzed part of the IDX — read these two articles before you design your metrics. Using
> `casa_ratio` without knowing what CASA means is exactly the kind of thing a judge from a
> banking-veteran-led team will notice.

One concept worth flagging: **Loan at Risk (LAR)** is broader than NPL — it captures
restructured-but-currently-performing loans that NPL alone misses. The screener exposes both
`non_performing_loan` and `restructured_loan_current`, so **you can compute LAR yourself**.
That is a derived metric with a real definition behind it — precisely the kind of thing
Track 03 asks for, and it costs 1 credit.

---

## 2. Referral program → API credits (and the hackathon caution)

The [Community Bulletin](https://sectors.app/bulletin) confirms what the API-for-IDX FAQ
hinted at:

> "When your friends join Sectors through your referral link — or enter your referral code
> during sign up, you will be credited with points. **Redeem your points for rewards, API
> credits and Sectors merchandise.**"

Merchandise is also awarded for any of:

- Completing the practicum on the Financial API Workshops
- **Creating remarkable tutorials or guides featuring Sectors datasets**
- Referring 6 or more friends
- Signing up for an annual subscription

There is also a **Student-Ambassador program**, open to Indonesian *and Malaysian* university
students — relevant given the hackathon's campus-partner list.

> ⚠️ **Same caution as before.** The hackathon rules make "registering additional accounts to
> obtain extra credits for the same project" a disqualifying offence. A genuine referral is
> not multi-accounting, but referring your own teammates to top up the team's credits sits
> close enough to that line to be a bad trade. Ask in Slack `#support` before doing it.
>
> The "create remarkable tutorials or guides ft. Sectors datasets" reward is entirely safe, and
> notably it is the same thing the hackathon rewards — a well-documented public repo.

---

## 3. Stories — what good Market Intelligence output looks like

[Stories](https://sectors.app/story) is Sectors' editorial desk: *"Deep dives into ownership
trails, exits, and the deals reshaping Indonesia's listed companies."*

Recent pieces (August 2026):

| Date | Story | Built on |
| --- | --- | --- |
| Aug 19 | **"IMPC's 1.45 billion-share block never left the family"** — record profits two years running, stock down 66% from January highs | Ownership + price |
| Aug 13 | **"Indonesian Tycoons"** — three family empires taking different paths with controlling stakes | Ownership, conglomerate groups |
| Aug 13 | **"DSSA releases its buyback shares as profit keeps falling"** — 9.63 billion treasury shares back to market | Treasury/buyback + financials |

**Read these as Track 03 calibration.** They are the organizers demonstrating what they
consider a good derived insight: a specific, named, surprising claim about a specific company,
supported by joining two or three datasets. Not a dashboard — a *finding*.

Notice what all three are built on: **ownership structure, controlling stakes, treasury
shares, family/group relationships**. That is the `shareholders-composition`,
`major_shareholders_*` screener fields, and conglomerate-group territory — and per
[`already-published.md`](../04-build-plan/already-published.md), none of it has a code recipe.

---

## 4. Their search architecture — free engineering calibration

[Architectural Notes for our Financial Search Engine](https://sectors.app/bulletin/search-architecture)
is a 17-minute technical write-up by Samuel Chan (June 2026) on how Sectors Search Console
works. Worth reading because it shows, concretely, what this team considers good engineering —
which is the standard your 30% technical-depth score is judged against.

The design, in brief:

- **Search runs entirely in the browser.** The corpus is built offline, refreshed ~twice weekly, shipped to the client and indexed in-memory. No network round trip for the common case.
- **Progressive indexing.** The IDX index builds synchronously on mount; conglomerates load lazily; SGX waits on a small fetch of valid tickers. Readiness is per-index — no global ready gate, so the experience degrades gracefully.
- **All fields collapse under one identifier.** Ticker, name and description are indexed under the ticker. Simple retrieval, deliberately pushing complexity into ranking.
- **Command-palette scoping.** `/sg banks` or `/id ...` parses before touching the index — scoping never costs a model call or network hop.
- **Tiered comparator instead of weighted scores.** They explicitly reject `1000*inFull + 100*inName + 10*inDesc` as brittle "magic numbers", in favour of a comparator where each `||` is a tier and a later signal only matters on a tie.
- **Relevance cutoff.** If any name-tier match exists, drop the description-only tail; if nothing matched a name, keep everything so a narrow query is never starved to empty.
- **Lite-IDF weighting** so a rare token (`pan`) outweighs a common one (`bank`) — the article's own example. (The worked illustration that follows from it — a `bank pan` query having to separate Bank Jago from Panin — is this dossier's, not theirs.)
- **Web workers** keep indexing and searching off the typing thread.

Two things to take from it:

**They value determinism and explainability over cleverness.** The stated reason for the
tiered comparator is that *"it had no match in the name and there were better matches
available"* is an answer they can stand behind, and an opaque score threshold is not. The same
argument appears in their data-ops page (explainable investability scores) and in the GNN
recipe (disclosed weights). **A project that can explain why it ranked something is arguing in
their language.**

**They publicly credit a user who found a bug.** The article notes the unranked-results problem
was "surfaced by @jigsawinthecity immediately". Small thing, but it tells you the team is
responsive in public — the Slack and Discord are worth using.

---

## 5. Scale and coverage figures, collected

Different pages quote different numbers. All of them, with sources:

| Figure | Value | Source |
| --- | --- | --- |
| Data points processed daily | **67,900+** | `/enterprise` |
| Live financial and AI workflows | **40,000/month** | `/enterprise`, footer |
| IDX companies indexed | **99.9%** | `/enterprise`, `/api-for-idx` |
| Indonesian economic sectors indexed | **100%**, IDX specifications | `/enterprise` |
| IDX listed companies | **960** (bulletin, Aug 2026) · **942** (API `/v2/close/` fixture) · "950+" (pricing) | varies by date |
| IDX headline market cap | **IDR 11,081T** | `/bulletin` |
| Workshop students | **1,577+** since 2020 · 12 workshops · **4.9/5** average rating · 500+ companies | `/financial-api-workshops` |

> Workshop recordings ship with an **Insider** membership, and Sectors currently has no
> workshops scheduled. Not directly useful during the hackathon window, but the practicum is
> one of the merchandise-earning tasks.

---

## 6. What the remaining footer links are

For completeness, every other footer destination, opened and classified:

| Link | What it is | Useful? |
| --- | --- | --- |
| `/search`, `/chat`, `/screener`, `/peers` | Product surfaces (login for full use) | Competitive context only |
| `/indonesia`, `/singapore`, `/malaysia` | Market landing pages | Product |
| `/indonesia/most-traded`, `/idx/broker`, `/idx/foreign-flow` | Market data pages — the product view of API endpoints already documented | Product |
| `/indonesia/group`, `/singapore/group` | Conglomerate/group pages (52 + 30) | **Data angle** — group structure is not directly an API endpoint |
| `/indonesia/bumn` | State-owned enterprise list | **Data angle** — government ownership shipped Apr 2026 |
| `/indonesia/economic-sectors`, `/indonesia/indeks` | Sector and index overviews | Product view of `/v2/subsectors/`, `/v2/index-daily/` |
| `/indonesia/news`, `/singapore/news` | News feeds | Product view of `/v2/news/` |
| `/indonesia/2026/latest` | IDX Weekly Digest | Editorial |
| `/indonesia/calendars/dividend-calendar` | Dividend calendar | Product view of corporate actions |
| `/indonesia/lists/*`, `/indonesia/*-indonesia` | 6 curated stock lists (largest, dividend, profitable, low P/E, gainers, YoY growth) | Product view of screener queries |
| `/privacy` | Privacy policy | Legal |
| `/sitemap.xml` | 2,006 URLs | Enumerated in pass 8 |
| `supertype.ai` | Parent company | Context |

None of these expose data the API does not, with the partial exception of **conglomerate
group structure** and **BUMN classification**, which appear as product features whose API
surface is limited to `shareholders-composition` and the `major_shareholders_*` /
`affiliates` screener fields. Test before building on them — same caveat as the Orderbook in
[`12-trading-calendar-and-releases.md`](12-trading-calendar-and-releases.md).
