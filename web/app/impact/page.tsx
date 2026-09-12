"use client";

import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useDataset, useEngine } from "@/lib/dataset";
import { useCatalystStore } from "@/lib/store";
import type { CausalGraph, MarketEvent, SymbolCode } from "@/lib/types";
import { CausalChain } from "@/components/causal-chain";
import { CitationDialog } from "@/components/citation-dialog";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { IconBranch, IconEmpty, IconFilter, IconWatch } from "@/components/ui/icons";
import { cn, formatAsOf } from "@/lib/utils";

/**
 * The three source families a KATALIS card actually reads. There is no macro, commodity,
 * weather or policy entry because no endpoint behind this product serves one, and a filter
 * for a source that cannot appear is a control that lies about the data.
 */
const sourceLabels: Record<Extract<MarketEvent["sourceType"], "sectors" | "filing"> | "market" | "all", string> = {
  all: "Semua endpoint",
  market: "Tape dan kepemilikan",
  sectors: "News",
  filing: "Filing dan aksi korporasi",
};

const selectClass = "h-11 w-full cursor-pointer appearance-none rounded-[6px] border border-border bg-surface pl-10 pr-3 text-[13px] outline-none transition-colors focus:border-foreground/40 focus:ring-2 focus:ring-ring/25";

function filterSource(graph: CausalGraph, sourceType: keyof typeof sourceLabels): CausalGraph {
  if (sourceType === "all") return graph;
  const sourceIds = new Set(graph.nodes.filter((node) => node.kind === "source" && node.sourceType === sourceType).map((node) => node.id));
  const mechanismIds = new Set(graph.edges.filter((edge) => sourceIds.has(edge.from)).map((edge) => edge.to));
  const keptIds = new Set(graph.nodes.filter((node) => node.kind === "company" || node.kind === "observation").map((node) => node.id));
  sourceIds.forEach((id) => keptIds.add(id));
  mechanismIds.forEach((id) => keptIds.add(id));
  return {
    ...graph,
    nodes: graph.nodes.filter((node) => keptIds.has(node.id)),
    edges: graph.edges.filter((edge) => keptIds.has(edge.from) && keptIds.has(edge.to)),
    hiddenRelationshipCount: graph.hiddenRelationshipCount + graph.nodes.filter((node) => node.kind === "source" && node.sourceType !== sourceType).length,
  };
}

function ImpactContent() {
  const searchParams = useSearchParams();
  const profile = useCatalystStore((state) => state.profile);
  const { companies } = useDataset();
  const engine = useEngine();
  const companyParam = searchParams.get("company")?.toUpperCase() as SymbolCode | undefined;
  const requestedSymbol = companies.some((company) => company.symbol === companyParam && company.analyzed) ? companyParam : undefined;
  const [scope, setScope] = useState<"watchlist" | "market">("watchlist");
  const [symbol, setSymbol] = useState<SymbolCode>(requestedSymbol ?? "");
  const [sourceType, setSourceType] = useState<keyof typeof sourceLabels>("all");
  const availableCompanies = useMemo(() => companies.filter((company) => company.analyzed && (scope === "market" || profile.watchlist.includes(company.symbol))), [companies, profile.watchlist, scope]);
  const activeSymbol = availableCompanies.some((company) => company.symbol === symbol) ? symbol : availableCompanies[0]?.symbol ?? symbol;
  const baseGraph = useMemo(() => activeSymbol ? engine.buildCausalGraph(activeSymbol, profile, { scope, minRelevance: 0 }) : null, [activeSymbol, engine, profile, scope]);
  const graph = useMemo(() => baseGraph ? filterSource(baseGraph, sourceType) : null, [baseGraph, sourceType]);
  const sourceNodes = (graph?.nodes ?? []).filter((node) => node.kind === "source");

  return (
    <div className="mx-auto max-w-[1320px]">
      <PageHeader
        eyebrow="Jalur bukti"
        title="Dari endpoint, ke pilar, ke verdict"
        description="Peta ini bukan peta sebab-akibat pasar. Ia memperlihatkan endpoint mana yang membawa angkanya, pilar mana yang membacanya, dan apa yang pilar itu simpulkan — satu rantai yang bisa diperiksa ujung ke ujung. Produk ini tidak memproduksi jalur dampak antar-emiten, jadi tidak ada yang digambar di sini."
        action={graph ? <CitationDialog citations={graph.nodes.flatMap((node) => node.citations)} label="Ledger seluruh chain" /> : null}
      />

      <div className="mb-6">
        <div className="grid gap-3 md:grid-cols-[1fr_1.2fr_1fr]">
          <fieldset className="flex min-h-11 items-center gap-1 rounded-[6px] border border-border bg-surface p-1">
            <legend className="sr-only">Cakupan perusahaan</legend>
            {(["watchlist", "market"] as const).map((item) => (
              <button key={item} onClick={() => setScope(item)} aria-pressed={scope === item} className={cn("min-h-9 flex-1 cursor-pointer rounded-[4px] px-3 text-[12px] capitalize transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", scope === item ? "bg-foreground font-medium text-background" : "text-muted-foreground hover:text-foreground")}>{item}</button>
            ))}
          </fieldset>
          <label className="relative">
            <span className="sr-only">Pilih emiten</span>
            <IconBranch className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <select value={activeSymbol} onChange={(event) => setSymbol(event.target.value as SymbolCode)} className={selectClass}>
              {availableCompanies.map((company) => <option key={company.symbol} value={company.symbol}>{company.symbol} · {company.name ?? "nama tidak ada"}</option>)}
            </select>
          </label>
          <label className="relative">
            <span className="sr-only">Filter sumber</span>
            <IconFilter className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <select value={sourceType} onChange={(event) => setSourceType(event.target.value as keyof typeof sourceLabels)} className={selectClass}>
              {(Object.keys(sourceLabels) as Array<keyof typeof sourceLabels>).map((item) => <option key={item} value={item}>{sourceLabels[item]}</option>)}
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-col gap-2 text-[12px] leading-[1.6] text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-start gap-2"><IconWatch className="mt-0.5 size-3.5 shrink-0" />Setiap node membawa citation-nya sendiri; tidak ada simpul tanpa field sumber.</p>
          {sourceType === "all"
            ? <span className="meta text-positive">Seluruh endpoint kartu ini tampil</span>
            : <button onClick={() => setSourceType("all")} className="min-h-9 cursor-pointer self-start rounded-[6px] px-2 font-medium text-foreground underline decoration-border underline-offset-4 transition-colors hover:decoration-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Tampilkan semua endpoint</button>}
        </div>
      </div>

      {graph ? (
        <CausalChain key={`${activeSymbol}-${sourceType}`} graph={graph} />
      ) : (
        <Panel className="px-6 py-16 text-center">
          <IconEmpty className="mx-auto size-6 text-muted-foreground" />
          <h2 className="editorial mt-5 text-[21px]">Belum ada kartu pada scope ini</h2>
          <p className="mt-2 text-[13px] text-muted-foreground">Pilih market, atau emiten lain yang kartunya lengkap. Tidak ada rantai pengganti yang dibuat.</p>
        </Panel>
      )}

      <Reveal className="mt-6">
        <Panel>
          <PanelHeader eyebrow="Field ledger" title={`Endpoint yang dibaca untuk ${activeSymbol || "—"}`} />
          {sourceNodes.length ? (
            <div className="cascade grid gap-px bg-border md:grid-cols-2">
              {sourceNodes.map((node) => (
                <article key={node.id} className="bg-surface px-5 py-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="meta text-muted-foreground">{node.sourceType}</span>
                    <span className="ml-auto font-mono text-[10px] tabular-nums text-muted-foreground">{node.citations.length} field</span>
                  </div>
                  <h3 className="mt-3 break-all font-mono text-[12.5px] font-medium leading-[1.5]">{node.label}</h3>
                  <p className="mt-2.5 break-words text-[12.5px] leading-[1.65] text-muted-foreground">{node.detail}</p>
                  <div className="mt-4 flex items-center justify-between gap-3">
                    <span className="meta text-muted-foreground">{graph?.asOf ? `${formatAsOf(graph.asOf)} WIB` : "—"}</span>
                    <CitationDialog citations={node.citations} label="Buka field" />
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="px-6 py-12 text-center text-[13px] text-muted-foreground">Tidak ada endpoint pada filter ini.</p>
          )}
        </Panel>
      </Reveal>
    </div>
  );
}

export default function ImpactPage() {
  return <Suspense fallback={<Panel className="h-96 animate-pulse" aria-label="Memuat causal impact explorer" />}><ImpactContent /></Suspense>;
}
