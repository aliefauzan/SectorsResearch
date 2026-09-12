import "server-only";

import { EMPTY_DATASET, type Dataset } from "@/lib/katalis/dataset";
import { toAnalysis, toCompany } from "@/lib/katalis/map";
import type { KatalisCard, KatalisSymbolRow, KatalisSymbols } from "@/lib/katalis/types";
import type { AnalysisCase } from "@/lib/types";

export function apiBaseUrl(): string {
  return (
    process.env.KATALIS_API ??
    process.env.NEXT_PUBLIC_KATALIS_API ??
    "https://katalis-api-ibyebnreqa-et.a.run.app"
  );
}

async function getJson<T>(url: string): Promise<{ ok: true; data: T } | { ok: false; reason: string }> {
  try {
    // `revalidate` rather than `no-store`: the underlying payloads are recordings with a
    // fixed `as_of`, so a five-minute window cannot serve a stale number — it can only
    // avoid re-reading the same files on every navigation.
    const response = await fetch(url, { headers: { accept: "application/json" }, next: { revalidate: 300 } });
    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const body = (await response.json()) as { error?: string };
        if (body?.error) detail = body.error;
      } catch {
        // A non-JSON error body is not more informative than the status line.
      }
      return { ok: false, reason: detail };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return { ok: false, reason: error instanceof Error ? error.message : String(error) };
  }
}

/**
 * One symbol's card, asked for at a date the broker tape actually covers.
 *
 * Asking without a date gets the last trading day, and on the recorded source that is a day
 * no broker summary was ever captured for — so every symbol but one would come back refused
 * for a reason that says nothing about the symbol. The listing publishes where the tape is;
 * this walks those dates newest first, stops at the first card, and keeps the last refusal
 * so the screen can print the real cause instead of "not found".
 */
async function fetchCard(baseUrl: string, row: KatalisSymbolRow) {
  const path = (date?: string) =>
    `${baseUrl}/json/card/${encodeURIComponent(row.symbol)}${date ? `?date=${encodeURIComponent(date)}` : ""}`;
  const dates = row.broker_dates.slice().reverse();
  if (dates.length === 0) return getJson<KatalisCard>(path());
  let last = await getJson<KatalisCard>(path(dates[0]));
  for (const date of dates.slice(1)) {
    if (last.ok) return last;
    last = await getJson<KatalisCard>(path(date));
  }
  return last;
}

export async function loadDataset(): Promise<Dataset> {
  const baseUrl = apiBaseUrl();
  const listing = await getJson<KatalisSymbols>(`${baseUrl}/json/symbols`);
  if (!listing.ok) {
    return { ...EMPTY_DATASET, baseUrl, error: `KATALIS API tidak dapat dihubungi: ${listing.reason}` };
  }

  const rows = listing.data.symbols;
  const cards = await Promise.all(rows.map(async (row) => ({ symbol: row.symbol, result: await fetchCard(baseUrl, row) })));

  const analyses: Record<string, AnalysisCase> = {};
  const rejected: Record<string, string> = {};
  for (const { symbol, result } of cards) {
    if (result.ok) analyses[symbol] = toAnalysis(result.data);
    else rejected[symbol] = result.reason;
  }

  const companies = rows.map((row) => analyses[row.symbol]?.company ?? toCompany(row));
  const dates = Object.values(analyses).map((analysis) => analysis.asOf).filter(Boolean);

  return {
    source: listing.data.source,
    baseUrl,
    asOf: dates.length ? dates.slice().sort().at(-1)! : null,
    companies,
    analyses,
    rejected,
    error: null,
  };
}
