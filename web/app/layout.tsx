import type { Metadata } from "next";
import { Geist, Geist_Mono, Newsreader } from "next/font/google";
// React Flow's stylesheet first, so the overrides in globals.css win without
// needing to fight it on specificity.
import "@xyflow/react/dist/style.css";
import "./globals.css";
import { Providers } from "@/components/providers";
import { AppShell } from "@/components/app-shell";
import { loadDataset } from "@/lib/katalis/load";

const sans = Geist({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });
const editorial = Newsreader({ subsets: ["latin"], variable: "--font-editorial", weight: ["400", "500"], style: ["normal", "italic"], display: "swap" });

export const metadata: Metadata = {
  title: { default: "Catalyst", template: "%s | Catalyst" },
  description: "Permukaan baca untuk kartu empat pilar KATALIS, langsung dari Sectors API.",
};

/**
 * The root layout is where the market data enters the app, once.
 *
 * Everything below it is a client component — the profile, the watchlist and the review
 * notes live in the browser — so the cards are fetched here, on the server, and handed down
 * as one serialized dataset. No page fetches, and no component has a spinner for a number.
 */
export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const dataset = await loadDataset();
  return (
    <html lang="id" suppressHydrationWarning>
      <body className={`${sans.variable} ${mono.variable} ${editorial.variable} font-[family-name:var(--font-sans)] antialiased`}>
        <Providers dataset={dataset}><AppShell>{children}</AppShell></Providers>
      </body>
    </html>
  );
}
