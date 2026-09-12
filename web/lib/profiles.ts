import type { UserProfile } from "@/lib/types";

/**
 * The two demo profiles, and what a profile is allowed to change.
 *
 * A profile reorders the pillars and sets how much detail a card shows. It does not change a
 * number, an ambang, or a verdict — `pillars.py` decided those before the browser saw them,
 * and two people reading the same symbol on the same date must read the same card. That is
 * why `pillarOrder` and `depth` live here and nothing else does.
 *
 * The watchlists start empty on purpose. The symbols a deployment can serve come from
 * `GET /json/symbols`, which depends on which payloads have been paid for; a list hardcoded
 * here would name tickers the API cannot open. `components/providers.tsx` seeds the first
 * watchlist from the dataset the server loaded, and the setup wizard takes it from there.
 */
export const demoProfiles: UserProfile[] = [
  {
    id: "flow-first",
    name: "Flow-first",
    description: "Membaca konsentrasi partisipan lebih dulu, lalu volume.",
    watchlist: [],
    owned: [],
    config: { horizon: "event", depth: "standard", pillarOrder: ["concentration", "volume", "momentum", "catalyst"] },
    preferredSectors: [],
    preferredEventTypes: ["company", "commodity"],
    hasOnboarded: false,
  },
  {
    id: "catalyst-first",
    name: "Catalyst-first",
    description: "Mulai dari kabar dan filing, lalu memeriksa apakah tape mendukungnya.",
    watchlist: [],
    owned: [],
    config: { horizon: "swing", depth: "forensic", pillarOrder: ["catalyst", "momentum", "volume", "concentration"] },
    preferredSectors: [],
    preferredEventTypes: ["policy", "rates"],
    hasOnboarded: false,
  },
];
