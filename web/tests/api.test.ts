import { beforeEach, describe, expect, it } from "vitest";
import { POST as analyze } from "@/app/api/analyze/route";
import { POST as chat } from "@/app/api/chat/route";
import { POST as impact } from "@/app/api/impact/route";
import { demoProfiles } from "@/lib/profiles";
import { stubKatalisApi, LIFE } from "./helpers";

const profile = { ...demoProfiles[0], watchlist: [LIFE] };
const request = (path: string, body: unknown) => new Request(`http://localhost${path}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

beforeEach(() => stubKatalisApi());

describe("public route handlers", () => {
  it("returns a cited analysis for a symbol the API served", async () => {
    const response = await analyze(request("/api/analyze", { symbol: LIFE, profile }));
    const body = await response.json();
    expect(response.status).toBe(200);
    expect(body.analysis.verdict.length).toBeGreaterThan(0);
    expect(body.analysis.sources.length).toBeGreaterThan(0);
    expect(body.source).toBe("recorded");
  });

  it("returns 404 with the refusal reason instead of inventing an analysis", async () => {
    const response = await analyze(request("/api/analyze", { symbol: "BBCA", profile }));
    const body = await response.json();
    expect(response.status).toBe(404);
    expect(body.error).toContain("TIDAK DINILAI");
  });

  it("answers 501 on impact, because no event path is produced", async () => {
    const response = await impact(request("/api/impact", { eventId: "apa-saja", profile, scope: "watchlist" }));
    const body = await response.json();
    expect(response.status).toBe(501);
    expect(body.detail).toContain("tidak mengarangnya");
  });

  it("refuses an advisory prompt without echoing its transaction term", async () => {
    const response = await chat(request("/api/chat", { question: `Apakah saya harus beli ${LIFE}?`, profile }));
    const body = await response.json();
    expect(body.answer.refused).toBe(true);
    expect(body.answer.text.toLowerCase()).not.toContain("beli ");
  });
});
