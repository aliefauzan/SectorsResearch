"use client";

import Link from "next/link";
import { useDataset, useEngine } from "@/lib/dataset";
import { useCatalystStore } from "@/lib/store";
import type { SymbolCode } from "@/lib/types";
import { formatAsOf, formatCurrency, formatPercentChange, orDash } from "@/lib/utils";
import { AgentTrace } from "@/components/agent-trace";
import { AnalysisReview } from "@/components/analysis-review";
import { CitationDialog } from "@/components/citation-dialog";
import { EvidenceCard } from "@/components/evidence-card";
import { PriceChart } from "@/components/price-chart";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  IconArrowLeft,
  IconAttention,
  IconBranch,
  IconCaretRight,
  IconCopilot,
  IconScales,
  IconThumbsDown,
  IconThumbsUp,
  IconUnknown,
} from "@/components/ui/icons";

const backLinkClass = "inline-flex min-h-10 items-center gap-2 rounded-[4px] text-[13px] text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

export function CompanyDetailClient({ symbol }: { symbol: SymbolCode }) {
  const { profile, recordFeedback, setCopilotOpen } = useCatalystStore();
  const dataset = useDataset();
  const engine = useEngine();
  const company = dataset.companies.find((item) => item.symbol === symbol);
  const analysis = engine.analyzeCompany(symbol, profile);

  if (!company) return (
    <div className="mx-auto max-w-[1180px]">
      <Link href="/companies" className={`mb-7 ${backLinkClass}`}><IconArrowLeft className="size-4" />Kembali ke Companies</Link>
      <Panel className="px-6 py-16 text-center">
        <IconUnknown className="mx-auto size-7 text-muted-foreground" />
        <h1 className="editorial mt-6 text-[23px]">{symbol} tidak dilayani sumber ini</h1>
        <p className="mx-auto mt-3 max-w-lg text-[13px] leading-[1.7] text-muted-foreground">Sumber <span className="font-mono">{dataset.source || "—"}</span> hanya memuat simbol yang payload-nya sudah ada di cakram. Tidak ada panggilan baru yang dibuat untuk menebak sisanya.</p>
      </Panel>
    </div>
  );

  if (!analysis) return (
    <div className="mx-auto max-w-[1180px]">
      <Link href="/companies" className={`mb-7 ${backLinkClass}`}><IconArrowLeft className="size-4" />Kembali ke Companies</Link>
      <Panel className="overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-6 py-6">
          <div>
            <p className="meta text-muted-foreground">IDX · {orDash(company.sector)}</p>
            <h1 className="editorial mt-2.5 text-[30px]">{company.symbol} <span className="text-muted-foreground">{orDash(company.name)}</span></h1>
          </div>
          <StatusBadge status="Tidak dinilai" />
        </div>
        <div className="px-6 py-14 text-center sm:py-20">
          <IconUnknown className="mx-auto size-7 text-muted-foreground" />
          <h2 className="editorial mt-6 text-[23px]">Analisis empat pilar belum tersedia</h2>
          <p className="mx-auto mt-3 max-w-lg text-[13px] leading-[1.7] text-muted-foreground">{dataset.rejected[company.symbol] ?? "Deret harga ada, tetapi salah satu prasyarat pilar belum terpenuhi pada tanggal itu."} Produk ini menolak menilai alih-alih mengarang angka pengganti.</p>
          <div className="mt-7 flex justify-center"><CitationDialog citations={company.citations} label="Periksa snapshot" /></div>
        </div>
      </Panel>
    </div>
  );

  return (
    <div className="mx-auto max-w-[1180px]">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link href="/companies" className={backLinkClass}><IconArrowLeft className="size-4" />Companies</Link>
        <div className="flex w-full max-w-full flex-wrap gap-2 sm:w-auto">
          <Link href={`/impact?company=${symbol}`} className="inline-flex min-h-9 cursor-pointer items-center gap-2 rounded-[6px] border border-border bg-surface px-3 text-[12px] font-medium transition-colors hover:border-foreground/30 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <IconBranch className="size-3.5" />Lihat causal chain
          </Link>
          <CitationDialog citations={analysis.sources} />
          <Button variant="secondary" size="sm" onClick={() => setCopilotOpen(true)} className="xl:hidden"><IconCopilot className="size-3.5" />Tanya agent</Button>
        </div>
      </div>

      <header className="mb-6 rounded-[12px] border border-border bg-surface px-6 py-7 sm:px-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="meta text-muted-foreground">IDX:{company.symbol} · {orDash(company.sector)} · {orDash(company.subsector)}</p>
            <h1 className="editorial mt-3 text-[32px] sm:text-[40px]">{orDash(company.name)}</h1>
            <p className="meta mt-3 text-muted-foreground">asOf {formatAsOf(analysis.asOf)} WIB</p>
          </div>
          <div className="shrink-0 sm:text-right">
            <p className="font-mono text-[30px] font-light leading-none tabular-nums">{company.price === null ? "—" : formatCurrency(company.price)}</p>
            <p className={`mt-2.5 font-mono text-[13px] tabular-nums ${company.changePct === null ? "text-muted-foreground" : company.changePct >= 0 ? "text-positive" : "text-danger"}`}>{formatPercentChange(company.changePct)} · {dataset.source}</p>
            <div className="mt-3 sm:flex sm:justify-end"><StatusBadge status={analysis.evidenceState} /></div>
          </div>
        </div>
        <div className="mt-7 grid gap-5 border-t border-border pt-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div>
            <p className="meta text-muted-foreground">Evidence summary</p>
            <p className="mt-2 max-w-3xl text-[14px] leading-[1.7]">{analysis.thesis}</p>
          </div>
          <p className="meta shrink-0 rounded-full bg-muted px-3 py-1.5 text-muted-foreground">No combined score</p>
        </div>
      </header>

      <PriceChart data={analysis.priceSeries} symbol={symbol} />

      <section aria-labelledby="pillars-title" className="mt-10">
        <div className="mb-5 flex items-end justify-between gap-4 border-b border-border pb-4">
          <div>
            <p className="meta text-muted-foreground">Personalized order</p>
            <h2 id="pillars-title" className="editorial mt-2 text-[24px]">Empat pilar bukti</h2>
          </div>
          <Link href="/agent" className="inline-flex min-h-9 shrink-0 items-center gap-1.5 text-[12px] text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Ubah urutan<IconCaretRight className="size-3.5" /></Link>
        </div>
        <Reveal>
          <div className="cascade grid gap-5 md:grid-cols-2">
            {analysis.pillars.map((pillar, index) => <EvidenceCard key={pillar.key} pillar={pillar} index={index} />)}
          </div>
        </Reveal>
      </section>

      <Reveal className="mt-6">
        <Panel>
          <details className="group">
            <summary className="flex min-h-16 cursor-pointer list-none items-center gap-4 px-5 py-4 transition-colors hover:bg-muted/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
              <IconScales className="size-4 shrink-0 text-muted-foreground" />
              <span className="min-w-0 flex-1">
                <span className="meta block text-muted-foreground">Ambang · {analysis.thresholds.length} dipakai pada kartu ini</span>
                <span className="mt-1 block text-[13.5px] font-medium">Angka yang memutuskan setiap status, dan dari mana asalnya</span>
              </span>
              <span className="hidden text-[12px] text-muted-foreground sm:block">shipped = ditulis tangan · learned = dipelajari</span>
              <span aria-hidden="true" className="font-mono text-[15px] leading-none text-muted-foreground">
                <span className="group-open:hidden">+</span>
                <span className="hidden group-open:inline">−</span>
              </span>
            </summary>
            <div className="border-t border-border px-5 py-5">
              <table className="w-full text-left text-[12.5px]">
                <caption className="sr-only">Ambang yang dipakai kartu {symbol}</caption>
                <thead>
                  <tr className="border-b border-border">
                    <th className="meta py-2 pr-4 font-normal text-muted-foreground">Ambang</th>
                    <th className="meta py-2 pr-4 text-right font-normal text-muted-foreground">Nilai</th>
                    <th className="meta py-2 font-normal text-muted-foreground">Asal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono tabular-nums">
                  {analysis.thresholds.map((entry) => (
                    <tr key={entry.name}>
                      <td className="py-2 pr-4">{entry.name}</td>
                      <td className="py-2 pr-4 text-right">{entry.value}</td>
                      <td className="py-2 font-[family-name:var(--font-sans)]"><StatusBadge status={entry.origin} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-4 text-[12px] leading-[1.65] text-muted-foreground">Kartu memakai classifier <span className="font-mono">{analysis.classifier}</span> pada jendela {analysis.window[0]}..{analysis.window.at(-1)}. Mengubah profil tidak mengubah satu pun baris di atas.</p>
            </div>
          </details>
        </Panel>
      </Reveal>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(280px,0.7fr)]">
        <Reveal><AgentTrace traces={analysis.hypotheses} /></Reveal>
        <Reveal index={1}>
          <Panel className="h-full">
            <PanelHeader eyebrow="Fail closed" title="Belum diperiksa" />
            <ul className="divide-y divide-border">
              {analysis.missingEvidence.map((item) => (
                <li key={item} className="flex gap-3 px-5 py-3.5 text-[12.5px] leading-[1.65] text-muted-foreground">
                  <IconAttention className="mt-1 size-3.5 shrink-0 text-attention" />{item}
                </li>
              ))}
            </ul>
            <p className="border-t border-border px-5 py-4 text-[11.5px] leading-[1.6] text-muted-foreground">Kekosongan data tidak diisi dengan estimasi tersembunyi.</p>
          </Panel>
        </Reveal>
      </div>

      <Reveal className="mt-6"><AnalysisReview symbol={symbol} /></Reveal>

      <Reveal className="mt-6">
        <Panel>
          <PanelHeader eyebrow="Personal memory" title="Apakah susunan ini membantu?" />
          <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-2xl text-[12.5px] leading-[1.7] text-muted-foreground">Feedback mengubah ranking, urutan, atau kedalaman pada kunjungan berikutnya. Angka, formula, sumber, dan safety gate tetap.</p>
            <div className="flex shrink-0 gap-2">
              <Button variant="secondary" size="sm" onClick={() => recordFeedback({ symbol, action: "useful" })}><IconThumbsUp className="size-3.5" />Berguna</Button>
              <Button variant="secondary" size="sm" onClick={() => recordFeedback({ symbol, action: "not-useful" })}><IconThumbsDown className="size-3.5" />Kurangi</Button>
            </div>
          </div>
        </Panel>
      </Reveal>
    </div>
  );
}
