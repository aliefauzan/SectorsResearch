import { beforeEach, describe, expect, it } from "vitest";
import { createEngine } from "@/lib/agent/engine";
import { type Dataset } from "@/lib/katalis/dataset";
import { loadDataset } from "@/lib/katalis/load";
import { demoProfiles } from "@/lib/profiles";
import { stubKatalisApi, LIFE } from "./helpers";

const profile = { ...demoProfiles[0], watchlist: [LIFE] };
let dataset: Dataset;

beforeEach(async () => {
  stubKatalisApi();
  dataset = await loadDataset();
});

describe("dataset", () => {
  it("serves a card for the symbol whose broker tape was captured", () => {
    expect(dataset.analyses[LIFE]).toBeDefined();
    expect(dataset.companies.length).toBe(9);
  });

  it("keeps the refusal reason for a symbol it could not assess", () => {
    const refused = Object.values(dataset.rejected);
    expect(refused.length).toBeGreaterThan(0);
    expect(refused[0]).toContain("TIDAK DINILAI");
  });
});

describe("agent engine", () => {
  it("reorders pillars per profile without changing a figure", () => {
    const engine = createEngine(dataset);
    const flow = engine.analyzeCompany(LIFE, demoProfiles[0])!;
    const catalystFirst = engine.analyzeCompany(LIFE, { ...demoProfiles[1], watchlist: [LIFE] })!;
    expect(flow.pillars[0].key).toBe("concentration");
    expect(catalystFirst.pillars[0].key).toBe("catalyst");
    expect(flow.verdict).toBe(catalystFirst.verdict);
    const figures = (analysis: typeof flow) =>
      analysis.pillars.flatMap((pillar) => pillar.metrics.map((metric) => `${metric.label}=${metric.value}`)).sort();
    expect(figures(flow)).toEqual(figures(catalystFirst));
  });

  it("gives every metric a provider, endpoint, field, and asOf", () => {
    const analysis = createEngine(dataset).analyzeCompany(LIFE, profile)!;
    for (const pillar of analysis.pillars) {
      for (const metric of pillar.metrics) {
        expect(metric.citations.length).toBeGreaterThan(0);
        for (const citation of metric.citations) {
          expect(citation.provider).toBe("Sectors");
          expect(citation.endpoint).toMatch(/^\/v2\//);
          expect(citation.field.length).toBeGreaterThan(0);
          expect(citation.asOf).toBe(analysis.asOf);
        }
      }
    }
  });

  it("returns null rather than inventing a card", () => {
    expect(createEngine(dataset).analyzeCompany("ZZZZ", profile)).toBeNull();
  });

  it("maps no event impact, because the product produces none", () => {
    expect(createEngine(dataset).mapEventImpact("apa-saja", profile, "market")).toBeNull();
  });

  it("builds an evidence chain whose every node carries a citation", () => {
    const graph = createEngine(dataset).buildCausalGraph(LIFE, profile, { scope: "watchlist", minRelevance: 0 })!;
    expect(graph.nodes.some((node) => node.kind === "company")).toBe(true);
    expect(graph.nodes.filter((node) => node.kind === "mechanism")).toHaveLength(4);
    expect(graph.nodes.filter((node) => node.kind === "source").length).toBeGreaterThan(0);
    for (const node of graph.nodes) expect(node.citations.length).toBeGreaterThan(0);
    for (const edge of graph.edges) {
      expect(graph.nodes.some((node) => node.id === edge.from)).toBe(true);
      expect(graph.nodes.some((node) => node.id === edge.to)).toBe(true);
    }
  });
});

describe("copilot answers", () => {
  const ask = (question: string) =>
    createEngine(dataset).answerFollowUp({ question, profile, contextSymbol: LIFE });

  it("refuses an advisory question without echoing the transaction word", () => {
    const answer = ask(`apakah saya harus beli ${LIFE} sekarang?`);
    expect(answer.refused).toBe(true);
    expect(answer.intent).toBe("advice");
    expect(answer.text.toLowerCase()).not.toContain("beli ");
  });

  it("answers why a symbol is listed with its own verdict", () => {
    const answer = ask(`kenapa ${LIFE} masuk daftar?`);
    expect(answer.refused).toBe(false);
    expect(answer.intent).toBe("why-listed");
    expect(answer.text).toContain(dataset.analyses[LIFE].verdict);
    expect(answer.citations.length).toBeGreaterThan(0);
  });

  it("says plainly that event impact paths are not produced", () => {
    const answer = ask(`apa dampak berita itu ke ${LIFE}?`);
    expect(answer.intent).toBe("event-impact");
    expect(answer.text).toContain("tidak memproduksi jalur dampak");
  });

  it("names what was not checked when asked", () => {
    const answer = ask(`data apa yang belum diperiksa untuk ${LIFE}?`);
    expect(answer.intent).toBe("missing");
    expect(answer.text.length).toBeGreaterThan(20);
  });
});
