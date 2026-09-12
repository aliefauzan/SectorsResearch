import type { AnalysisCase, Company } from "@/lib/types";

/**
 * The dataset one render of the app reads. Built on the server, serialized into the client
 * tree once, and never refetched in the browser.
 *
 * Why the whole thing at once: every screen in this app is a view over the same nine cards,
 * and a card is a file read on the API side, not a market call — fetching them together
 * costs one round trip per symbol and zero Sectors credits. Nothing here is cached to disk
 * or committed; remove the API and the app has nothing to show, which is the dependency the
 * hackathon rules ask for.
 */
export interface Dataset {
  source: string;
  baseUrl: string;
  asOf: string | null;
  companies: Company[];
  analyses: Record<string, AnalysisCase>;
  /** Symbols the API served a listing row for but refused to assess, and the reason it gave. */
  rejected: Record<string, string>;
  /** Set when the API could not be reached at all. Every screen renders this instead of data. */
  error: string | null;
}

/** What a client reads before the server has handed it anything, and after a failed fetch. */
export const EMPTY_DATASET: Dataset = {
  source: "",
  baseUrl: "",
  asOf: null,
  companies: [],
  analyses: {},
  rejected: {},
  error: null,
};
