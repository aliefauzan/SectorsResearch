/**
 * A ticker this deployment can serve. Not a closed union any more: the list is whatever
 * `GET /json/symbols` returns for the source the API is pointed at, which is nine recorded
 * symbols today and a different set on `synth`. A union baked into the front end would have
 * to be edited every time a payload is bought, and would be wrong between the buy and
 * the edit.
 */
export type SymbolCode = string;

/** Whatever `company_report.overview.sector` says, or null when no report exists. */
export type Sector = string;

export type PillarKey = "concentration" | "volume" | "momentum" | "catalyst";
export type Horizon = "event" | "swing" | "position";
export type AnswerDepth = "compact" | "standard" | "forensic";
/**
 * The verdict `pillars.verdict()` produced — one of six mechanical names, not a score and
 * not a recommendation. It is a string here because the vocabulary lives in Python and the
 * card is the thing that defines it.
 */
export type EvidenceState = string;
export type ImpactDirection = "Supported" | "Adverse" | "Mixed" | "Unrelated" | "Unverified";

export interface Citation {
  id: string;
  provider: string;
  endpoint: string;
  field: string;
  asOf: string;
  label: string;
  url?: string;
  urlLabel?: string;
  access?: "direct" | "provider" | "documentation";
}

export interface MetricValue {
  label: string;
  value: string;
  detail?: string;
  citations: Citation[];
}

export interface PillarResult {
  key: PillarKey;
  label: string;
  status: string;
  summary: string;
  metrics: MetricValue[];
  citations: Citation[];
  /** What this pillar did not look at, in its own words. Empty when it looked at everything. */
  unchecked: string[];
  conflict?: string;
  calculation?: {
    name: string;
    formula: string;
    substitution: string;
    result: string;
    notes: string[];
  };
}

export interface FinancialInput {
  label: string;
  value: string;
  period: string;
  interpretation: string;
  citations: Citation[];
}

export interface Company {
  symbol: SymbolCode;
  /** The issuer name the payload carries, or null when no local payload happens to hold one. */
  name: string | null;
  sector: Sector | null;
  subsector: string | null;
  price: number | null;
  changePct: number | null;
  marketCap: number | null;
  /** Trading days on this source, and the window they span — the reader's honesty check. */
  days: number;
  window: { first: string | null; last: string | null };
  analyzed: boolean;
  evidenceState: EvidenceState;
  summary: string;
  asOf: string;
  citations: Citation[];
}

export interface PricePoint {
  date: string;
  close: number;
  /** Null on a date the index has no row for; the chart draws a gap rather than a guess. */
  ihsg: number | null;
  volume: number;
}

export interface BrokerEvidence {
  buyers: Array<{ code: string; origin: "local" | "foreign"; value: number }>;
  sellers: Array<{ code: string; origin: "local" | "foreign"; value: number }>;
  netForeign: number;
  totalMarketValue: number;
  freeFloatShares: number;
  sharesOutstanding: number;
  referencePrice: number;
}

export interface CompanyAnalysisFixture {
  symbol: SymbolCode;
  priceSeries: PricePoint[];
  broker: BrokerEvidence;
  sectorReturn: number;
  beta: number;
  catalystEventIds: string[];
  financialContext: FinancialInput[];
}

export interface HypothesisTrace {
  id: string;
  hypothesis: string;
  query: string;
  verification: string;
  outcome: "supported" | "challenged" | "open";
  citations: Citation[];
}

export interface AnalysisCase {
  company: Company;
  evidenceState: EvidenceState;
  thesis: string;
  pillars: PillarResult[];
  hypotheses: HypothesisTrace[];
  sources: Citation[];
  missingEvidence: string[];
  priceSeries: PricePoint[];
  financialContext: FinancialInput[];
  asOf: string;
  /** Everything below comes from the card and is shown verbatim, never recombined. */
  verdict: string;
  modifiers: string[];
  window: string[];
  classifier: string;
  thresholds: Array<{ name: string; origin: "shipped" | "learned"; value: number }>;
  unavailable: Array<{ path: string; reason: string }>;
}

export interface ImpactLink {
  symbol: SymbolCode;
  direction: ImpactDirection;
  relevance: number;
  path: string;
  rationale: string;
  citations: Citation[];
}

export interface MarketEvent {
  id: string;
  title: string;
  summary: string;
  category: "company" | "commodity" | "rates" | "currency" | "policy" | "weather";
  sourceType: "sectors" | "filing" | "macro" | "commodity" | "weather" | "policy";
  publishedAt: string;
  asOf: string;
  sector: Sector | "Market";
  impactLinks: ImpactLink[];
  citations: Citation[];
}

export interface AgentConfig {
  horizon: Horizon;
  depth: AnswerDepth;
  pillarOrder: PillarKey[];
}

export interface UserProfile {
  id: "flow-first" | "catalyst-first";
  name: string;
  description: string;
  watchlist: SymbolCode[];
  owned: SymbolCode[];
  config: AgentConfig;
  preferredSectors: Sector[];
  preferredEventTypes: MarketEvent["category"][];
  hasOnboarded: boolean;
}

export interface FeedbackEvent {
  id: string;
  symbol?: SymbolCode;
  eventId?: string;
  action: "useful" | "not-useful" | "show-more" | "show-less";
  createdAt: string;
}

export interface LearnedPreference {
  id: string;
  label: string;
  explanation: string;
  source: "explicit" | "feedback";
  active: boolean;
}

export interface UserInsight {
  id: string;
  symbol: SymbolCode;
  pillar?: PillarKey;
  category: "data-error" | "missing-context" | "alternative-interpretation";
  note: string;
  status: "pending" | "incorporated" | "dismissed";
  createdAt: string;
}

export interface ChatRequest {
  question: string;
  profile: UserProfile;
  contextSymbol?: SymbolCode;
  userInsights?: UserInsight[];
}

export interface ChatAnswer {
  text: string;
  refused: boolean;
  intent: "why-listed" | "event-impact" | "compare" | "missing" | "advice" | "unknown";
  hypotheses: HypothesisTrace[];
  citations: Citation[];
  preferenceNote: string;
  relatedSymbols: SymbolCode[];
}

export interface CausalNode {
  id: string;
  label: string;
  kind: "source" | "mechanism" | "company" | "observation";
  detail: string;
  sourceType?: MarketEvent["sourceType"] | "market" | "financial";
  direction?: ImpactDirection;
  relevance?: number;
  citations: Citation[];
}

export interface CausalEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  direction: ImpactDirection;
  relevance: number;
  citations: Citation[];
}

export interface CausalGraph {
  targetSymbol: SymbolCode;
  nodes: CausalNode[];
  edges: CausalEdge[];
  hiddenRelationshipCount: number;
  asOf: string;
}

export interface MarketDataProvider {
  listCompanies(): Company[];
  getCompany(symbol: string): Company | undefined;
  getDailySeries(symbol: string): PricePoint[];
  getBrokerEvidence(symbol: string): BrokerEvidence | undefined;
  getCompanyEvents(symbol: string): MarketEvent[];
}

export interface NewsProvider {
  listEvents(): MarketEvent[];
  getEvent(id: string): MarketEvent | undefined;
}

export interface AgentEngine {
  analyzeCompany(symbol: string, profile: UserProfile): AnalysisCase | null;
  mapEventImpact(eventId: string, profile: UserProfile, scope: "watchlist" | "market"): MarketEvent | null;
  answerFollowUp(request: ChatRequest): ChatAnswer;
  buildCausalGraph(symbol: string, profile: UserProfile, options: { scope: "watchlist" | "market"; minRelevance: number }): CausalGraph | null;
}

export interface MemoryStore {
  loadProfile(): UserProfile;
  recordFeedback(feedback: FeedbackEvent): void;
  recordInsight(insight: UserInsight): void;
  listInsights(): UserInsight[];
  listPreferences(): LearnedPreference[];
  compareProfiles(): UserProfile[];
  reset(): void;
}
