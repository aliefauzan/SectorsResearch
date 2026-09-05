# Authenticated browser session captures — 5 September 2026

Captured through the user's own logged-in Chrome session (free-tier Sectors account,
signed up via Google). No credentials were entered by Claude; the session was already
authenticated. These are the sources for quotes in `02-sectors-platform/03`, `/05`, `/11`
and `/14` that are not present in any other raw file.

---

## sectors.app/api → API Key Management  (free account)

Page state:
- Heading "API Key Management"
- Buttons: **Create Key**, **Usage and Balances**
- Table columns: Key | Name | Creation Date | **API Usage**
- Table body, verbatim:

> "Please upgrade your subscription to access Sectors API. Click here to see more."

- "Inactive API Keys" section: "You currently have no inactive API keys."

Conclusion: a free Sectors account cannot create an API key. The API is Insider-gated.
The "Usage and Balances" button + per-key "API Usage" column are the credit observability
shipped in the 2026-08-10 "Foreign Flows" release.

---

## sectors.app/api → API Playground

Three sub-tabs: **v2 Playground**, **Natural Language Query**, **Deterministic Query Builder**.

Intro copy, verbatim:

> "In-browser experimentation with various Sectors Financial API endpoints to understand their
> functionalities and responses. Whilst in Demo Mode (not signed in), the returned values are
> mock data to demonstate the data structure. Signing in with Sectors Insider allows you to use
> your API key to get actual data from Sectors."

> "Utilize the Query Builder feature to construct API requests that are deterministic and
> fitting for structured data retrieval and automation tasks. The query is a composition of
> SQL-like vocabulary, and can directly be copied from the Query Builder into your own
> applications."

The v2 Playground showed a "Demo Mode" badge next to each endpoint on this free account.
Endpoint navigator groups matched the OpenAPI tags exactly (Company Screener, Helper Lists,
Detailed Reports, Transaction Data, Rankings, IPO & Performance, News & Filings, Brokers,
then SINGAPORE (SGX) …).

---

## Deterministic Query Builder — full panel text

> "The Deterministic Query Builder is available through our v2 API (Detailed Documentation),
> and is the most powerful way to query our financial dataset albeit with an increased level
> of complexity."

> "Unlike the v1 endpoints, the Query Builder exposes a universal set of SQL-like vocabulary
> that can be used to compose request across multiple years, columns, companies, and even
> in-memory calculations"

Parameter table, verbatim:

| Parameter | Description |
| --- | --- |
| where | Filters the data based on specified conditions. |
| order_by | Sorts the results based on one or more columns. Prefix field with - for descending order (e.g., -revenue). |
| limit | Restricts the number of records returned. |
| offset | Skips a specified number of records before starting to return records. |
| include_query_values | Boolean (true/false) to include the query values in the response. |

**Concrete Example** — "The following is a valid endpoint call constructed through the Query
Builder mechanism:"

```
GET https://api.sectors.app/v2/companies/?where=sub_sector = "banks" and revenue[2024] > revenue[2022] * 1.21 and total_yield[2024] is not null&order_by=-total_yield[2024], market_cap&limit=10
```

**How the Query Builder Works** — verbatim:

> "Retrieves banks whose revenue[2024] > revenue[2022] * 1.21 (21% growth vs 2022 — a CAGR of
> 10% per year) and are dividend-paying (total_yield[2024] is not null). Results ordered by
> total_yield[2024] (desc), then market_cap (asc)."

WHERE clause as shown for use on the docs site:

```
sub_sector = "banks" and revenue[2024] > revenue[2022] * 1.21 and total_yield[2024] is not null
```

Builder UI: condition groups (GROUP 1) with AND / OR, "Add condition", "Add Group",
ORDER BY list with per-column DESC, LIMIT, OFFSET ("Skip the first N results — pair with
limit for pagination"). Note: "The Deterministic Query Builder is a work in progress — more
advanced features are on the way."

EQUIVALENT SQL-LIKE QUERY, verbatim:

```
SELECT * FROM sectors_v2 WHERE (sub_sector="banks" and eps[2024]>0 and total_yield[2024] is not null) ORDER BY -total_yield[2024], -market_cap LIMIT 20
```

GENERATED URL ENDPOINT / API KEY fields, and:

> "Generate CSV from Query — This operation costs 1 API credit, and is available on the
> Sectors Insider plans."

Sample Python shown:

```python
import requests

url = """https://api.sectors.app/v2/companies/?where=(sub_sector="banks" and eps[2024]>0 and total_yield[2024] is not null)&order_by=-total_yield[2024], -market_cap&limit=20&include_query_values=true
"""

headers = {"Authorization": "xxx-your-sectors-api-key-xxx"}

response = requests.get(url, headers=headers)

print(response.text)
```

Builder has separate 🇮🇩 IDX and 🇸🇬 SGX modes.

---

## sectors.app/data-operations — NPL standardisation example

Verbatim (annotation 2, "Standardization with good sense"):

> "Companies report their financial data in different formats and structures. Sometimes, the
> same data point is reported under a different name, or sorted differently whether erroneously
> or intentionally. An example is the treatment of "Non-performing Loans" in balance sheets of
> banking companies. Most companies report this figure having accounted for provision of
> restructured loans, but there are instances where this figure is reported following the
> collectibility classification without further consideration."

> "Our data operations consult with financial experts to determine the correct treatment for
> standardization whenever judgment is required, and document these decisions in our data
> dictionary for transparency and traceability."

---

## hackathon.sectors.app/portal/team (signed out of the hackathon portal)

Redirects to `/auth/sign-in?next=%2Fportal%2Fteam`. Page offers **Login with GitHub**,
**Login with Google**, or email/password, with the note:

> "Use the same Sectors Account you already use for datasets, APIs, and market intelligence."

Portal steps shown: 01 Register · 02 Form a team · 03 Submit.

Not proceeded past this point — no team was registered.
