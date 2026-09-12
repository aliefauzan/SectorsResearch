import { describe, expect, it } from "vitest";
import { enforceCitations, safeLanguage } from "@/lib/agent/gates";
import type { PillarResult } from "@/lib/types";

describe("agent output gates", () => {
  it("rejects a metric without provider, endpoint, field, and asOf", () => {
    const pillar = {
      key: "volume",
      label: "Volume",
      status: "Elevated",
      summary: "Aktivitas berada di atas baseline.",
      metrics: [{ label: "volume_z", value: "3,2", citations: [] }],
      citations: [],
      unchecked: [],
    } satisfies PillarResult;

    expect(() => enforceCitations([pillar])).toThrow("Citation gate");
  });

  it("refuses transaction advice and keeps the response evidence-based", () => {
    const answer = safeLanguage("apakah saya harus beli ANTM sekarang?");
    expect(answer.refused).toBe(true);
    expect(answer.text).toContain("tidak menilai tindakan transaksi");
    expect(answer.text.toLowerCase()).not.toContain("target price");
  });
});
