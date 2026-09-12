"use client";

import { createContext, useContext, useMemo } from "react";
import { createEngine } from "@/lib/agent/engine";
import type { AgentEngine } from "@/lib/types";
import { EMPTY_DATASET, type Dataset } from "@/lib/katalis/dataset";

/**
 * The server-loaded dataset, handed to the client tree once by the root layout.
 *
 * Every page in this app is a client component because the profile, the watchlist and the
 * review notes live in the browser. The market data does not: it is fetched on the server,
 * passed down here, and read synchronously from then on. That split is why no component has
 * a loading state for data it cannot compute anyway.
 */
const DatasetContext = createContext<Dataset>(EMPTY_DATASET);

export function DatasetProvider({ value, children }: { value: Dataset; children: React.ReactNode }) {
  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>;
}

export function useDataset(): Dataset {
  return useContext(DatasetContext);
}

/**
 * The agent, bound to the dataset this render was given. Memoised per dataset so a page that
 * calls it in several components does not rebuild the closure each time.
 */
export function useEngine(): AgentEngine {
  const dataset = useDataset();
  return useMemo(() => createEngine(dataset), [dataset]);
}
