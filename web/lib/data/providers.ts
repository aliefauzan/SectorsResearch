import type { Dataset } from "@/lib/katalis/dataset";
import type { MarketDataProvider, NewsProvider } from "@/lib/types";

/**
 * The provider seam, over the KATALIS API instead of a fixture file.
 *
 * `getCompanyEvents` and the whole news provider answer empty, and that is a statement about
 * the product rather than a gap in this file: KATALIS counts articles, filings and corporate
 * actions inside the event window and reports those counts through the katalis pillar, but it
 * publishes no event objects, no impact links and no relevance scores. A provider that
 * returned something here would be inventing the one thing the card refuses to assert.
 */
export function createMarketDataProvider(dataset: Dataset): MarketDataProvider {
  return {
    listCompanies: () => dataset.companies,
    getCompany: (symbol) => dataset.companies.find((company) => company.symbol === symbol.toUpperCase()),
    getDailySeries: (symbol) => dataset.analyses[symbol.toUpperCase()]?.priceSeries ?? [],
    getBrokerEvidence: () => undefined,
    getCompanyEvents: () => [],
  };
}

export const emptyNewsProvider: NewsProvider = {
  listEvents: () => [],
  getEvent: () => undefined,
};
