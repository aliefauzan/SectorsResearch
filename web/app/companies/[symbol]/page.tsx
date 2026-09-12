import { CompanyDetailClient } from "./company-detail-client";

/**
 * No `generateStaticParams`: which symbols exist is decided by `GET /json/symbols` at
 * request time, not at build time, and a build-time list would go stale the moment a payload
 * is bought. The client reads the dataset the root layout loaded and says so itself when the
 * symbol is not served.
 */
export default async function CompanyDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  return <CompanyDetailClient symbol={symbol.toUpperCase()} />;
}
