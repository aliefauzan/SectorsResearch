# Two Hidden Subdomains, and the Terms of Service

> Ninth-pass finding, from opening every footer link one by one.
>
> **Two of them are entire separate products on their own subdomains** — they do not appear in
> `sectors.app/sitemap.xml`, so the exhaustive sitemap enumeration in the previous pass could
> never have found them. The footer was the only route in.

---

## 1. `mining.sectors.app` — Sectors for Mining, Metals & Minerals

A full product, not a page. Self-described as *"an extension to Sectors Financial Data
Platform… API-first, Chat-queryable, and easily integrates into existing vector stores, LLMs,
and automation workflows."* Data updated May 2026.

**445 URLs**, structured as:

| Area | Contents |
| --- | --- |
| Four commodities | **Coal, Gold, Nickel, Copper** — each with `/companies`, `/sites`, a price page, and `/learn` guides |
| Price pages | `coal-mining/harga-batubara-acuan` (**HBA**), `gold-mining/gold-price`, `nickel-mining/nickel-price`, `copper-mining/copper-price` |
| Learn guides | **16 articles + 1 index page** (17 `/learn` URLs in the sitemap), four per commodity: a background piece, a quality/types piece, a price-and-royalty piece, and a glossary. Coal's four are titled **"Coal Mining in Indonesia Background"**, **"Types of Coal"**, **"HBA Coal Prices and Royalties"** and **"Coal Mining Glossary"**. Gold's price guide is **"LBMA Gold Prices"** |
| Insights | `/indonesia/insights/resources-and-reserves`, `/indonesia/insights/performance-metrics` |
| Global | `/global/exports`, `/global/production` |
| Company pages | ~400, by slug |
| Mining sites | By province — Kalimantan Timur, Kalimantan Selatan, Sumatera Selatan, Kalimantan Tengah, Jambi |

### Facts worth knowing

- **594 companies covered in coal alone.** The API's `/v2/mining/companies/` is the programmatic view of this.
- **Unlisted companies are genuinely in there.** The homepage shows Berau Coal explicitly tagged *"Not Listed on IDX"*, and company slugs include `kestrel-coal-resources`, `asia-pacific-nickel-pty-ltd`, `nickel-international-capital-pte`, `cv-mitra-perdana-equipment`. This substantiates the "private and unlisted companies" claim in a way the API docs never show.
- Coal is **6.6% of Indonesian GDP**; Indonesia is the **3rd largest coal producer** and **largest coal exporter** at **38.3% of global seaborne exports**. As of 2024: **97,960.76 Mt of coal resources, 31,955.5 Mt of reserves**.
- Key export markets: China, India, Japan. Key regions: East Kalimantan, South Kalimantan, South Sumatera.

### ⚠️ HBA is *not* in the API

The coal price benchmark **HBA (Harga Batubara Acuan)** — Indonesia's official coal price
reference, and the basis for royalty calculation — has a dedicated page on the mining product.

**It does not appear anywhere in the API documentation.** Searching all 820 KB of
`llms-full.txt` returns **zero** matches for `HBA`, `Harga`, or `acuan`. The API's
`/v2/mining/commodities/{commodity_name}/price/` returns a generic
`{name, date, price_usd_per_ton}` — not the HBA benchmark.

If your project premise is "track Indonesian coal against its official benchmark", the
benchmark is product-only. Verify before building.

### What the commodity price endpoint *does* give you

From the fixture for `/v2/mining/commodities/`:

```json
[{ "name": "Gold", "data_points": 703,
   "earliest_date": "1968-01-01", "latest_date": "2026-07-01" }]
```

**Gold price history back to 1968** — 703 monthly data points, nearly 60 years. That is by
far the longest time series anywhere in this API, and no recipe uses it. Note the endpoint
caps a single request at a **3-year range**, so a full pull is ~20 calls.

---

## 2. `reits.sectors.app` — Sectors · REITs

A second full product. *"A neutral analyst terminal for Singapore-listed REITs (S-REITs)."*
Filing data through Jul 2026.

**118 URLs**: 37 REIT profiles, 8 sub-sector pages, 31 country pages, 37 glossary entries,
2 articles, a screener, a start-here guide.

| Metric | Value |
| --- | --- |
| S-REITs covered | **37** |
| Combined market cap | **S$95.46B** — 7.0% of total SGX market cap |
| Properties | **3,420 across 30 countries** |
| Median dividend yield | **6.6%** (TTM) |
| Sub-sectors | Diversified (11), Industrial (6), Retail (6), Office (5), Hospitality (5), Healthcare (2), Data Centre (2) |
| Geography | 75% of properties sit **outside** Singapore; 15 REITs are entirely overseas. Top: Singapore 866, US 480, Japan 367, Australia 348, UK 262, China 209 |

Metrics tracked per trust: **gearing, occupancy, distribution per unit (DPU), WALE,
portfolio value, price-to-NAV, P/B, distribution yield**.

### ⚠️ REITs has no API at all

The word "API" does not appear anywhere on the REITs site, there is no REIT endpoint in the
70-endpoint v2 spec, and no REIT fields in either screener.

`reits.sectors.app` publishes its own [`llms.txt`](https://reits.sectors.app/llms.txt)
(11.5 KB, saved to [`../99-raw/reits-llms.txt`](../99-raw/reits-llms.txt)) — useful if you
want an LLM to reason about S-REITs, but it is a page index, not a data feed.

**Do not plan a REITs project for this hackathon.** The rules require Sectors MCP or the
Sectors REST API as a *core data source*, and there is no REIT data in either. A REIT project
would fail the eligibility check.

---

## 3. ⚠️ The Terms of Service restrict commercial use

From <https://sectors.app/terms-of-service>, quoted directly:

> "Any commercial use of our Services, including but not limited to our paid offerings, our
> Sectors Financial API subscription, and other features or components included within the
> Services, is **strictly prohibited** unless you are in a custom agreement with us through
> our Sectors for Enterprise offering."

Commercial use is defined to include:

> "the integration, incorporation, display, distribution or utilization of the Services or
> Content within any commercial product, service, website, application, or platform"

and

> "Use the Services as part of any effort to compete with us or otherwise use the Services
> and/or the Content for any revenue-generating endeavor or commercial enterprise."

There is also an anti-automation clause prohibiting any "spider, robot, cheat utility, scraper,
or offline reader" beyond standard search-engine or browser usage.

### What this means for the hackathon

**For the event itself, nothing changes.** The licence granted is for "personal,
non-commercial use or for the internal business use of your company" — a hackathon prototype,
a public demo repo and a judging video sit inside that. The organizers are running the
competition and granting the credits, so participation is plainly authorised.

**It matters afterwards.** If you win and want to turn the project into a product, a paid
service, or anything revenue-generating, the ToS points you at **Sectors for Enterprise**
(help@sectors.app) for a custom agreement. That is worth knowing before you promise a
commercial roadmap in your judging video.

It also interacts with two hackathon rules in a way worth noting:

- The rules require your repo to stay **public for 90 days** and grant Sectors promotional rights, while **IP stays entirely with you**. None of that conflicts with the ToS — but the ToS restricts what you may do with *their data*, not with your code.
- Any "competes with us" reading is a reason to avoid rebuilding Sectors Workflow or the screener as your project — a point already argued on product grounds in [`../04-build-plan/competitive-landscape.md`](../04-build-plan/competitive-landscape.md).

> This is a plain reading of a public terms page, not legal advice. If your plans go beyond
> the hackathon, ask in Slack `#support` or email help@sectors.app rather than relying on
> this summary.

---

## Why the footer mattered

The previous pass enumerated `sectors.app/sitemap.xml` — 2,006 URLs — and concluded the
domain was exhausted. That conclusion was wrong in a specific way: **`mining.sectors.app` and
`reits.sectors.app` are different hosts and appear in no sectors.app sitemap.** Only the
footer links to them.

Corrected surface inventory:

| Host | Enumerated | Captured |
| --- | --- | --- |
| `hackathon.sectors.app` | 7 public pages | ✅ all |
| `sectors.app` | 2,006 sitemap URLs | ✅ all informational pages |
| `docs.sectors.app` | 140 sitemap URLs | ✅ 69/69 v2 pages |
| **`mining.sectors.app`** | **445 sitemap URLs** | ✅ structure + key pages |
| **`reits.sectors.app`** | **118 sitemap URLs** | ✅ structure + `llms.txt` |

Both new subdomains were then checked for hidden data feeds: `reits` has `llms.txt` but no
`llms-full.txt` and no API; `mining` has neither `llms.txt` nor `llms-full.txt`, and its data
is exposed through the 19 mining endpoints already documented in
[`02-endpoint-reference.md`](02-endpoint-reference.md).
