"use client";

import { useEffect } from "react";
import { ThemeProvider } from "next-themes";
import * as Tooltip from "@radix-ui/react-tooltip";
import { DatasetProvider } from "@/lib/dataset";
import type { Dataset } from "@/lib/katalis/dataset";
import { useCatalystStore } from "@/lib/store";

/**
 * Seeds an empty watchlist from the symbols this deployment can actually serve.
 *
 * `lib/profiles.ts` ships both demo profiles with an empty watchlist, because the tickers
 * available depend on which payloads have been paid for. This runs once, after the server
 * has told the client what the API serves, and only when the user has not chosen yet — a
 * watchlist the user edited is never overwritten.
 */
function WatchlistSeed({ dataset }: { dataset: Dataset }) {
  const watchlist = useCatalystStore((state) => state.profile.watchlist);
  const setWatchlist = useCatalystStore((state) => state.setWatchlist);
  useEffect(() => {
    if (watchlist.length > 0) return;
    // Carded symbols first, then the rest: a source may have bought the tape for only one or
    // two of them, and a watchlist of one is not a watchlist. The unanalysed ones are still
    // worth listing — their page says why they were refused.
    const carded = dataset.companies.filter((company) => company.analyzed).map((company) => company.symbol);
    const rest = dataset.companies.filter((company) => !company.analyzed).map((company) => company.symbol);
    const seeded = [...carded, ...rest].slice(0, 8);
    if (seeded.length) setWatchlist(seeded);
  }, [dataset.companies, setWatchlist, watchlist.length]);
  return null;
}

export function Providers({ dataset, children }: { dataset: Dataset; children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} storageKey="catalyst:theme">
      <DatasetProvider value={dataset}>
        <WatchlistSeed dataset={dataset} />
        <Tooltip.Provider delayDuration={250}>{children}</Tooltip.Provider>
      </DatasetProvider>
    </ThemeProvider>
  );
}
