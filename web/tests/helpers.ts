import { vi } from "vitest";
import symbols from "./fixtures/symbols.json";
import card from "./fixtures/card-LIFE.json";
import refusal from "./fixtures/refusal-BBCA.json";

/**
 * The KATALIS API, answering from payloads it really produced.
 *
 * These three files were written by `src/katalis/jsonapi.py` itself — the symbol listing, one
 * served card, and one refusal — so a shape change on the Python side breaks these tests
 * rather than sliding past them. They are a recording of the surface, not a hand-written
 * idea of what it returns, and nothing in them was typed by hand.
 */
export function stubKatalisApi() {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    const json = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
    if (url.includes("/json/symbols")) return json(symbols);
    if (url.includes("/json/card/LIFE")) return json(card);
    if (url.includes("/json/card/")) return json(refusal, 404);
    return json({ ok: false, error: "tidak ada rute itu" }, 404);
  }));
}

export const LIFE = card.symbol;
