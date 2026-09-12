/**
 * The shapes `src/katalis/jsonapi.py` actually serves.
 *
 * These are transcribed from that module's `document()` and `symbols_response()`, not
 * guessed: every field below exists because a gate over there requires it to exist. When
 * the surface grows a field, this file is the first place the change has to land, and
 * `lib/katalis/map.ts` is the second.
 *
 * Nothing here is optional-by-convenience. A value the product does not produce is `null`
 * on the wire and `null` in the type, and the reason it is null arrives in `unavailable`.
 */

/** One figure a pillar built. `value` is whatever `pillars.py` put in it — never re-derived. */
export interface KatalisMetric {
  name: string;
  value: number | string | Record<string, number> | null;
  unit: string;
  note: string | null;
  endpoint: string;
  fields: string[];
}

export interface KatalisPillar {
  name: "konsentrasi" | "volume" | "momentum" | "katalis";
  status: string;
  headline: string;
  metrics: KatalisMetric[];
  unchecked: string[];
  /** Always null: the pillars emit figures and notes, never a formula/substitution pair. */
  calculation: null;
}

export interface KatalisPricePoint {
  date: string;
  close: number;
  /** IHSG close on the same date, or null when the index has no row that day. */
  ihsg: number | null;
  volume: number;
}

export interface KatalisBrokerRow {
  date: string;
  code: string;
  net_idr: number;
  buy_idr: number;
  sell_idr: number;
  net_lot: number | null;
  avg_buy_price: number | null;
  origin_inline: string | null;
  cohort_inline: string | null;
  name: string | null;
  is_foreign: boolean | null;
  cohort: string | null;
}

export interface KatalisBroker {
  window: string[];
  rows: KatalisBrokerRow[];
  foreignFlow: Array<Record<string, unknown>> | null;
  buyers: null;
  sellers: null;
  netForeign: null;
  totalMarketValue: null;
  freeFloatShares: null;
  referencePrice: null;
}

export interface KatalisThreshold {
  name: string;
  origin: "shipped" | "learned";
  value: number;
}

export interface KatalisUnavailable {
  path: string;
  reason: string;
}

/**
 * `company_report.overview`, narrowed by `sources.company_profile` to six fields and gated
 * there. Null when the source has no company report (`synth` never does) or the report has
 * no overview — one recorded symbol is like that, and the screen has to render the absence
 * rather than fill it.
 */
export interface KatalisProfile {
  sector: string | null;
  sub_sector: string | null;
  market_cap: number | null;
  last_close_price: number | null;
  latest_close_date: string | null;
  daily_close_change: number | null;
}

export interface KatalisCard {
  ok: true;
  source: string;
  symbol: string;
  name: string | null;
  profile: KatalisProfile | null;
  as_of: string;
  classifier: string;
  decision: { verdict: string; modifiers: string[]; window: string[] };
  price_series: KatalisPricePoint[];
  broker: KatalisBroker;
  free_float: number | null;
  shares_outstanding: { value: number | null; fields: string[]; exact: boolean };
  pillars: KatalisPillar[];
  modifier_metrics: KatalisMetric[];
  thresholds: KatalisThreshold[];
  unavailable: KatalisUnavailable[];
}

export interface KatalisSymbolRow {
  symbol: string;
  name: string | null;
  profile: KatalisProfile | null;
  days: number;
  first: string | null;
  last: string | null;
  last_close: number | null;
  last_volume: number | null;
  /**
   * Dates the broker tape covers. Not a promise that a card exists on any of them — the
   * baseline can still be too short — so a caller walks them newest first and reads the
   * refusal the card route gives.
   */
  broker_dates: string[];
}

export interface KatalisSymbols {
  ok: true;
  source: string;
  symbols: KatalisSymbolRow[];
}

export interface KatalisError {
  ok: false;
  error: string;
}
