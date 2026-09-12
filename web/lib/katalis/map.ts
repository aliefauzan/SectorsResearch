/**
 * The one place a KATALIS reply becomes the shapes the screen renders.
 *
 * Two rules, and they are the same two `src/katalis/jsonapi.py` holds itself to:
 *
 *  1. **No arithmetic.** Nothing here adds, divides, averages or re-derives. Every number on
 *     screen is a value `pillars.assess()` produced, carried across and formatted. The one
 *     transformation applied to a figure is `formatFigure`, which is a transcription of
 *     `card._number` — the formatter the text card itself uses — so a number on the page and
 *     the same number on `./run.sh pilar` are the same characters.
 *  2. **No invention.** A field the reply carries as null stays null and the component shows
 *     the absence. The reasons are in the reply's own `unavailable` list and are rendered,
 *     not summarised away.
 */
import type {
  AnalysisCase,
  Citation,
  Company,
  HypothesisTrace,
  MetricValue,
  PillarKey,
  PillarResult,
  PricePoint,
} from "@/lib/types";
import type { KatalisCard, KatalisMetric, KatalisPillar, KatalisSymbolRow } from "@/lib/katalis/types";

const PILLAR_KEY: Record<KatalisPillar["name"], PillarKey> = {
  konsentrasi: "concentration",
  volume: "volume",
  momentum: "momentum",
  katalis: "catalyst",
};

const PILLAR_LABEL: Record<KatalisPillar["name"], string> = {
  konsentrasi: "Konsentrasi",
  volume: "Volume",
  momentum: "Momentum",
  katalis: "Katalis",
};

const idID = (options: Intl.NumberFormatOptions) => new Intl.NumberFormat("id-ID", options);

/**
 * `card._number`, transcribed.
 *
 * The Python is the original and this is the copy, so the order of the branches matters: a
 * dict sorts by descending share, `fraksi` switches format at 0.1, IDR and `lembar` are
 * grouped integers, and a bare float keeps two decimals. `check_json_number_matches_the_text_card`
 * on the API side asserts that the values this function receives are the ones the card
 * printed; keeping the formatting identical is what makes that assertion visible to a reader.
 */
export function formatFigure(metric: KatalisMetric): string {
  const { value, unit } = metric;
  if (value === null) return "—";
  if (typeof value === "object") {
    return Object.entries(value)
      .sort((first, second) => second[1] - first[1])
      .map(([key, share]) => `${key} ${idID({ style: "percent", maximumFractionDigits: 0 }).format(share)}`)
      .join(", ");
  }
  if (typeof value === "string") return value;
  if (unit === "fraksi" || unit === "fraksi float") {
    const digits = Math.abs(value) < 0.1 ? 2 : 1;
    return idID({ style: "percent", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  }
  if (unit === "IDR") return `Rp${idID({ maximumFractionDigits: 0 }).format(value)}`;
  if (unit === "lembar") return idID({ maximumFractionDigits: 0 }).format(value);
  if (Number.isInteger(value)) return idID({}).format(value);
  return idID({ minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

/**
 * One citation per (endpoint, field) the figure names.
 *
 * The figure already carries its own provenance — `pillars.py` refuses to build a `Figure`
 * without an endpoint and a field list — so this is a re-shaping, not a lookup. That is why
 * the citation gate in `lib/agent/gates.ts` can stay strict: a metric without a source here
 * would mean a figure without a source there, which the Python would not have built.
 */
function toCitations(metric: KatalisMetric, asOf: string): Citation[] {
  return metric.fields.map((field) => ({
    id: `${metric.endpoint}#${field}@${asOf}`,
    provider: "Sectors",
    endpoint: metric.endpoint,
    field,
    asOf,
    label: metric.name,
    url: `https://api.sectors.app${metric.endpoint}`,
    urlLabel: "Sectors API",
    access: "provider" as const,
  }));
}

function uniqueCitations(values: Citation[]): Citation[] {
  return [...new Map(values.map((citation) => [citation.id, citation])).values()];
}

function toMetric(metric: KatalisMetric, asOf: string): MetricValue {
  return {
    label: metric.name,
    value: formatFigure(metric),
    detail: metric.note ?? undefined,
    citations: toCitations(metric, asOf),
  };
}

export function toPillar(pillar: KatalisPillar, asOf: string): PillarResult {
  const metrics = pillar.metrics.map((metric) => toMetric(metric, asOf));
  return {
    key: PILLAR_KEY[pillar.name],
    label: PILLAR_LABEL[pillar.name],
    status: pillar.status,
    summary: pillar.headline,
    metrics,
    unchecked: pillar.unchecked,
    citations: uniqueCitations(metrics.flatMap((metric) => metric.citations)),
    // The reply carries `calculation: null` on every pillar and says why under `unavailable`:
    // the pillars emit figures and notes, never a formula/substitution pair. The card shows
    // each figure's own note instead, which is the nearest honest thing.
    calculation: undefined,
  };
}

/** A company row from the listing: name and profile, with no card fetched yet. */
export function toCompany(row: KatalisSymbolRow): Company {
  return {
    symbol: row.symbol,
    name: row.name,
    sector: row.profile?.sector ?? null,
    subsector: row.profile?.sub_sector ?? null,
    price: row.profile?.last_close_price ?? row.last_close ?? null,
    changePct: row.profile?.daily_close_change ?? null,
    marketCap: row.profile?.market_cap ?? null,
    days: row.days,
    window: { first: row.first, last: row.last },
    analyzed: false,
    evidenceState: "Belum dinilai",
    summary: "",
    asOf: row.last ?? "",
    citations: row.profile
      ? [{
          id: `/v2/company/report/${row.symbol}/#overview@${row.profile.latest_close_date ?? row.last ?? ""}`,
          provider: "Sectors",
          endpoint: `/v2/company/report/${row.symbol}/`,
          field: "overview.sector, overview.market_cap, overview.last_close_price",
          asOf: row.profile.latest_close_date ?? row.last ?? "",
          label: "Company report overview",
          url: "https://api.sectors.app/v2/company/report/",
          urlLabel: "Sectors API",
          access: "provider",
        }]
      : [],
  };
}

/**
 * The hypotheses a card answers, built from the pillars that answered them.
 *
 * Catalyst's planner shows four standing hypotheses and what each one was checked against.
 * Ours are the same four questions the four pillars ask, and the verification text is the
 * pillar's own headline — not a second sentence written here about the same evidence.
 */
function toHypotheses(symbol: string, pillars: PillarResult[]): HypothesisTrace[] {
  const questions: Record<PillarKey, { hypothesis: string; query: string }> = {
    concentration: {
      hypothesis: "Gerak didukung konsentrasi partisipan yang dapat diverifikasi.",
      query: "Broker summary, registry broker, foreign flow, free float",
    },
    volume: {
      hypothesis: "Aktivitas menyimpang dari kebiasaan simbol itu sendiri.",
      query: "Daily volume terhadap baseline 45 hari bursa (median dan MAD)",
    },
    momentum: {
      hypothesis: "Gerak tidak cukup dijelaskan oleh IHSG.",
      query: "Daily close, index-daily IHSG, beta efektif, residual",
    },
    catalyst: {
      hypothesis: "Ada kabar, filing, atau aksi korporasi yang menjelaskan gerak.",
      query: "News, filings, corporate actions dalam jendela peristiwa",
    },
  };
  return pillars.map((pillar) => ({
    id: `${symbol}-${pillar.key}`,
    hypothesis: questions[pillar.key].hypothesis,
    query: questions[pillar.key].query,
    verification: pillar.summary,
    outcome: pillar.status === "bahaya" ? "supported" : pillar.status === "tenang" ? "challenged" : "open",
    citations: pillar.citations,
  }));
}

/** The card as the screen reads it. Pillar order is canonical here; the profile reorders it. */
export function toAnalysis(card: KatalisCard): AnalysisCase {
  const pillars = card.pillars.map((pillar) => toPillar(pillar, card.as_of));
  const company: Company = {
    symbol: card.symbol,
    name: card.name,
    sector: card.profile?.sector ?? null,
    subsector: card.profile?.sub_sector ?? null,
    price: card.price_series.at(-1)?.close ?? card.profile?.last_close_price ?? null,
    changePct: card.profile?.daily_close_change ?? null,
    marketCap: card.profile?.market_cap ?? null,
    days: card.price_series.length,
    window: { first: card.price_series[0]?.date ?? null, last: card.price_series.at(-1)?.date ?? null },
    analyzed: true,
    evidenceState: card.decision.verdict,
    summary: pillars[0]?.summary ?? "",
    asOf: card.as_of,
    citations: uniqueCitations(pillars.flatMap((pillar) => pillar.citations)),
  };

  const priceSeries: PricePoint[] = card.price_series.map((point) => ({
    date: point.date,
    close: point.close,
    ihsg: point.ihsg,
    volume: point.volume,
  }));

  return {
    company,
    evidenceState: card.decision.verdict,
    thesis: card.decision.modifiers.length
      ? `${card.decision.verdict}. ${card.decision.modifiers.join(" · ")}.`
      : `${card.decision.verdict}.`,
    pillars,
    hypotheses: toHypotheses(card.symbol, pillars),
    sources: company.citations,
    missingEvidence: [
      ...pillars.flatMap((pillar) => pillar.unchecked),
      ...card.unavailable.map((entry) => `${entry.path}: ${entry.reason}`),
    ],
    priceSeries,
    financialContext: [],
    asOf: card.as_of,
    verdict: card.decision.verdict,
    modifiers: card.decision.modifiers,
    window: card.decision.window,
    classifier: card.classifier,
    thresholds: card.thresholds,
    unavailable: card.unavailable,
  };
}
