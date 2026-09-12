import { describe, expect, it } from "vitest";
import { formatFigure, toAnalysis } from "@/lib/katalis/map";
import type { KatalisCard } from "@/lib/katalis/types";
import card from "./fixtures/card-LIFE.json";

const life = card as unknown as KatalisCard;

describe("figure formatting", () => {
  it("renders a fraction the way the text card renders it", () => {
    expect(formatFigure({ name: "pangsa_puncak", value: 0.647, unit: "fraksi", note: null, endpoint: "/v2/x/", fields: ["a"] })).toBe("64,7%");
    expect(formatFigure({ name: "float_terserap", value: 0.00034, unit: "fraksi float", note: null, endpoint: "/v2/x/", fields: ["a"] })).toBe("0,03%");
  });

  it("sorts a cohort split by descending share, as the card does", () => {
    const rendered = formatFigure({
      name: "pangsa_kohort",
      value: { institutional: 0.28, mixed: 0.07, retail: 0.65 },
      unit: "", note: null, endpoint: "/v2/x/", fields: ["a"],
    });
    expect(rendered).toBe("retail 65%, institutional 28%, mixed 7%");
  });

  it("shows an em dash for a figure the product does not produce", () => {
    expect(formatFigure({ name: "apa_saja", value: null, unit: "", note: null, endpoint: "/v2/x/", fields: [] })).toBe("—");
  });
});

describe("card mapping", () => {
  const analysis = toAnalysis(life);

  it("carries the four pillars in the card's own order", () => {
    expect(analysis.pillars.map((pillar) => pillar.key)).toEqual(["concentration", "volume", "momentum", "catalyst"]);
  });

  it("never fabricates a calculation block the reply says is unavailable", () => {
    for (const pillar of analysis.pillars) expect(pillar.calculation).toBeUndefined();
    expect(analysis.unavailable.some((entry) => entry.path === "pillars[].calculation")).toBe(true);
  });

  it("keeps every declared-unavailable field null on the wire", () => {
    expect(life.broker.buyers).toBeNull();
    expect(life.broker.netForeign).toBeNull();
    expect(life.broker.referencePrice).toBeNull();
  });

  it("carries the verdict and its markers verbatim", () => {
    expect(analysis.verdict).toBe(life.decision.verdict);
    expect(analysis.modifiers).toEqual(life.decision.modifiers);
  });
});
