import { assertSafeOutput, enforceCitations, safeLanguage } from "@/lib/agent/gates";
import type { Dataset } from "@/lib/katalis/dataset";
import type {
  AgentEngine,
  AnalysisCase,
  CausalGraph,
  ChatAnswer,
  ChatRequest,
  Citation,
  HypothesisTrace,
  PillarResult,
  SymbolCode,
  UserInsight,
  UserProfile,
} from "@/lib/types";

/**
 * The agent, over cards the API already decided.
 *
 * Catalyst's original engine computed HHI, robust z-scores and beta-adjusted residuals in
 * TypeScript. This one computes none of them, and that is the point: every figure on screen
 * was produced by `src/katalis/pillars.py`, cited by `jsonapi.py`, and checked by the gates
 * on that side. What remains here is the work a front end should do — ordering by profile,
 * routing a question to the pillar that answers it, and refusing to answer what the data
 * does not support.
 *
 * There is no `median`, no `**`, no accumulator over market values anywhere in this file.
 * A reviewer looking for the place a second, drifting derivation could hide should find
 * nothing to read.
 */

function uniqueCitations(values: Citation[]): Citation[] {
  return [...new Map(values.map((citation) => [citation.id, citation])).values()];
}

/** The same case the API served, with the pillars in the order this profile asked for. */
function analyze(dataset: Dataset, symbol: SymbolCode, profile: UserProfile): AnalysisCase | null {
  const analysis = dataset.analyses[symbol.toUpperCase()];
  if (!analysis) return null;
  const ordered = profile.config.pillarOrder
    .map((key) => analysis.pillars.find((pillar) => pillar.key === key))
    .filter((pillar): pillar is PillarResult => Boolean(pillar));
  const pillars = ordered.length === analysis.pillars.length ? ordered : analysis.pillars;
  enforceCitations(pillars);
  assertSafeOutput(analysis.thesis);
  return { ...analysis, pillars };
}

/**
 * The evidence path behind one verdict: endpoint → pillar → company.
 *
 * This is deliberately not a map of market causality. The product does not produce event
 * impact links, relevance scores, or exposure paths, and inventing them to fill this screen
 * is exactly the kind of fabrication the card refuses elsewhere. What it does produce is a
 * chain that can be checked end to end: which Sectors endpoint carried the numbers, which
 * pillar read them, and what that pillar concluded. Every node here names a real citation.
 */
function buildEvidenceGraph(dataset: Dataset, symbol: SymbolCode, profile: UserProfile,
                            options: { scope: "watchlist" | "market" }): CausalGraph | null {
  const analysis = analyze(dataset, symbol, profile);
  if (!analysis) return null;
  if (options.scope === "watchlist" && !profile.watchlist.includes(analysis.company.symbol)) return null;

  const companyId = `company-${analysis.company.symbol}`;
  const nodes: CausalGraph["nodes"] = [{
    id: companyId,
    label: analysis.company.symbol,
    kind: "company",
    detail: `${analysis.company.name ?? "Nama tidak ada di payload"} · verdict ${analysis.verdict}`,
    citations: analysis.sources,
  }];
  const edges: CausalGraph["edges"] = [];

  for (const pillar of analysis.pillars) {
    const pillarId = `mechanism-${pillar.key}`;
    nodes.push({
      id: pillarId,
      label: pillar.label,
      kind: "mechanism",
      detail: pillar.summary,
      sourceType: "market",
      relevance: 100,
      citations: pillar.citations,
    });
    edges.push({
      id: `${pillarId}-to-${companyId}`,
      from: pillarId,
      to: companyId,
      label: pillar.status,
      direction: "Unverified",
      relevance: 100,
      citations: pillar.citations,
    });

    const endpoints = [...new Set(pillar.citations.map((citation) => citation.endpoint))];
    for (const endpoint of endpoints) {
      const sourceId = `source-${endpoint}`;
      const cited = pillar.citations.filter((citation) => citation.endpoint === endpoint);
      if (!nodes.some((node) => node.id === sourceId)) {
        nodes.push({
          id: sourceId,
          label: endpoint,
          kind: "source",
          detail: `Field: ${cited.map((citation) => citation.field).join(", ")}`,
          sourceType: endpoint.includes("/filings") ? "filing" : endpoint.includes("/news") ? "sectors" : "market",
          relevance: 100,
          citations: cited,
        });
      }
      const edgeId = `${sourceId}-to-${pillarId}`;
      if (!edges.some((edge) => edge.id === edgeId)) {
        edges.push({ id: edgeId, from: sourceId, to: pillarId, label: "membaca", direction: "Unverified", relevance: 100, citations: cited });
      }
    }
  }

  for (const modifier of analysis.modifiers) {
    const modifierId = `observation-${modifier}`;
    nodes.push({
      id: modifierId,
      label: modifier,
      kind: "observation",
      detail: "Penanda verdict: dihitung oleh pillars.verdict() dari figure yang sama.",
      sourceType: "market",
      relevance: 100,
      citations: analysis.sources,
    });
    edges.push({ id: `${companyId}-to-${modifierId}`, from: companyId, to: modifierId, label: "penanda", direction: "Unverified", relevance: 100, citations: analysis.sources });
  }

  return { targetSymbol: analysis.company.symbol, nodes, edges, hiddenRelationshipCount: 0, asOf: analysis.asOf };
}

function findSymbols(dataset: Dataset, question: string): SymbolCode[] {
  const upper = question.toUpperCase();
  return dataset.companies.map((company) => company.symbol).filter((symbol) => new RegExp(`\\b${symbol}\\b`).test(upper));
}

function relevantInsights(insights: UserInsight[] | undefined, symbol?: SymbolCode): UserInsight[] {
  if (!symbol) return [];
  return (insights ?? []).filter((insight) => insight.symbol === symbol && insight.status !== "dismissed");
}

function insightTraces(insights: UserInsight[]): HypothesisTrace[] {
  return insights.map((insight) => ({
    id: insight.id,
    hypothesis: `Catatan user meminta verifikasi ulang${insight.pillar ? ` pada pilar ${insight.pillar}` : ""}.`,
    query: "Bandingkan catatan user dengan sumber sebelum menggabungkannya.",
    verification: "Belum diverifikasi. Catatan disimpan sebagai hipotesis personal, bukan fakta pasar.",
    outcome: "open",
    citations: [],
  }));
}

function preferenceNote(profile: UserProfile, insightCount = 0): string {
  const first = profile.config.pillarOrder[0];
  const collaboration = insightCount ? ` ${insightCount} catatan user terkait dimasukkan sebagai hipotesis terbuka.` : "";
  return `Urutan dimulai dari ${first}; profil ${profile.name} memilih kedalaman ${profile.config.depth}. Angka, ambang, dan verdict tidak berubah.${collaboration}`;
}

/**
 * A question routed to the pillar that answers it, or refused.
 *
 * Four intents survive from Catalyst's original six. `event-impact` does not, because the
 * product serves no event impact links: a question about what a piece of news did to a
 * ticker is answered by naming the katalis pillar's own counts and saying what is not
 * served, not by narrating a path that no payload supports.
 */
function answerFollowUp(dataset: Dataset, request: ChatRequest): ChatAnswer {
  const guarded = safeLanguage(request.question);
  const symbols = findSymbols(dataset, request.question);
  const primary = symbols[0] ?? request.contextSymbol;
  const analysis = primary ? analyze(dataset, primary, request.profile) : null;
  const insights = relevantInsights(request.userInsights, primary);
  const openTraces = insightTraces(insights);
  const note = preferenceNote(request.profile, insights.length);

  if (guarded.refused) {
    return {
      text: guarded.text, refused: true, intent: "advice",
      hypotheses: [...(analysis?.hypotheses ?? []), ...openTraces],
      citations: analysis?.sources.slice(0, 4) ?? [],
      preferenceNote: note, relatedSymbols: primary ? [primary] : [],
    };
  }

  const question = request.question.toLowerCase();

  if ((question.includes("banding") || question.includes("versus")) && symbols.length >= 2) {
    const first = analyze(dataset, symbols[0], request.profile);
    const second = analyze(dataset, symbols[1], request.profile);
    if (first && second) {
      return {
        text: `${first.company.symbol}: ${first.verdict} pada ${first.asOf}. ${second.company.symbol}: ${second.verdict} pada ${second.asOf}. Keduanya dibaca dengan ambang yang sama; kartunya memuat angka dan field di balik setiap status.`,
        refused: false, intent: "compare",
        hypotheses: [...first.hypotheses.slice(0, 1), ...second.hypotheses.slice(0, 1)],
        citations: uniqueCitations([...first.sources.slice(0, 3), ...second.sources.slice(0, 3)]),
        preferenceNote: note, relatedSymbols: [first.company.symbol, second.company.symbol],
      };
    }
  }

  if (question.includes("belum") || question.includes("data apa") || question.includes("tidak diperiksa") || question.includes("kosong")) {
    return {
      text: analysis
        ? analysis.missingEvidence.slice(0, 3).join(" ")
        : "Produk ini tidak memeriksa kanal di luar cakupannya, tidak memakai data intraday, dan tidak memproduksi jalur dampak peristiwa. Daftar lengkapnya ada pada setiap kartu.",
      refused: false, intent: "missing",
      hypotheses: [...(analysis?.hypotheses.filter((item) => item.outcome === "open") ?? []), ...openTraces],
      citations: analysis?.sources.slice(0, 3) ?? [],
      preferenceNote: note, relatedSymbols: primary ? [primary] : [],
    };
  }

  if (question.includes("berita") || question.includes("dampak") || question.includes("katalis")) {
    const catalyst = analysis?.pillars.find((pillar) => pillar.key === "catalyst");
    return {
      text: catalyst
        ? `${catalyst.summary} Produk ini menghitung kabar, filing, dan aksi korporasi di dalam jendela peristiwa; ia tidak memproduksi jalur dampak antar-emiten, jadi pertanyaan "berita ini menggerakkan apa" tidak dijawab di sini.`
        : "Tanpa ticker, pilar katalis tidak dapat dibaca. Sebutkan satu simbol yang ada di daftar.",
      refused: false, intent: "event-impact",
      hypotheses: [...(analysis?.hypotheses.filter((item) => item.id.endsWith("catalyst")) ?? []), ...openTraces],
      citations: catalyst?.citations.slice(0, 4) ?? [],
      preferenceNote: note, relatedSymbols: primary ? [primary] : [],
    };
  }

  if (analysis) {
    return {
      text: `${analysis.company.symbol} pada ${analysis.asOf} dibaca sebagai ${analysis.verdict}. ${analysis.thesis} Pilar pertama mengikuti profil Anda: ${analysis.pillars[0].label} — ${analysis.pillars[0].summary}`,
      refused: false, intent: "why-listed",
      hypotheses: [...analysis.hypotheses, ...openTraces],
      citations: analysis.sources, preferenceNote: note, relatedSymbols: [analysis.company.symbol],
    };
  }

  return {
    text: "Belum ada kartu untuk menjawab itu. Sebutkan satu simbol yang dilayani sumber ini, atau tanyakan apa yang belum diperiksa.",
    refused: false, intent: "unknown", hypotheses: [], citations: [], preferenceNote: note, relatedSymbols: [],
  };
}

/** The engine is built per dataset, because there is no data without one. */
export function createEngine(dataset: Dataset): AgentEngine {
  return {
    analyzeCompany: (symbol, profile) => analyze(dataset, symbol, profile),
    // The product serves no market events, so there is no event to map. Returning null is
    // what makes the screen say so instead of drawing an empty chart.
    mapEventImpact: () => null,
    answerFollowUp: (request) => answerFollowUp(dataset, request),
    buildCausalGraph: (symbol, profile, options) => buildEvidenceGraph(dataset, symbol, profile, options),
  };
}
