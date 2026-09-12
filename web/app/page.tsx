"use client";

import Link from "next/link";
import { useDataset, useEngine } from "@/lib/dataset";
import { useCatalystStore } from "@/lib/store";
import { formatAsOf, formatNumber } from "@/lib/utils";
import { CitationDialog } from "@/components/citation-dialog";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { StatusBadge } from "@/components/ui/status-badge";
import { IconArrowRight, IconCopilot, IconGate, IconSignal, IconSource, IconWatch } from "@/components/ui/icons";

export default function DashboardPage() {
  const { profile, insights, feedback } = useCatalystStore();
  const dataset = useDataset();
  const engine = useEngine();
  const { companies, analyses, source, asOf } = dataset;
  const rankedWatchlist = [...profile.watchlist].sort((first, second) => {
    const rank = (symbol: (typeof profile.watchlist)[number]) =>
      insights.filter((item) => item.symbol === symbol && item.status === "pending").length * 100
      + feedback.filter((item) => item.symbol === symbol && (item.action === "useful" || item.action === "show-more")).length * 10
      - feedback.filter((item) => item.symbol === symbol && (item.action === "not-useful" || item.action === "show-less")).length * 10;
    return rank(second) - rank(first);
  });
  const cases = rankedWatchlist
    .map((symbol) => engine.analyzeCompany(symbol, profile))
    .filter((item) => item !== null)
    .slice(0, 4);
  const citations = cases.flatMap((item) => item.sources);

  // Every number below is counted off the cards this render was given. None of them is a
  // constant, and none of them survives the API going away — which is the dependency the
  // product is supposed to have on Sectors.
  const flagged = Object.values(analyses).filter((analysis) =>
    analysis.pillars.some((pillar) => pillar.status === "bahaya"));
  const markers = Object.values(analyses)
    .filter((analysis) => profile.watchlist.includes(analysis.company.symbol) && analysis.modifiers.length)
    .slice(0, 4);
  const latestIhsg = Object.values(analyses)
    .flatMap((analysis) => analysis.priceSeries)
    .filter((point) => point.ihsg !== null)
    .sort((first, second) => first.date.localeCompare(second.date))
    .at(-1);
  const thresholds = Object.values(analyses)[0]?.thresholds ?? [];
  const learned = thresholds.filter((entry) => entry.origin === "learned").length;

  const ledger = [
    { label: "Kartu dibaca", value: String(cases.length), detail: "dari watchlist aktif" },
    { label: "Pilar menyala", value: String(flagged.length), detail: "punya sedikitnya satu bahaya" },
    { label: "Emiten dilayani", value: String(companies.length), detail: `sumber ${source || "—"}` },
    { label: "Data as of", value: asOf ?? "—", detail: "tanggal kartu terbaru" },
  ];

  return (
    <div className="mx-auto max-w-[1180px]">
      <PageHeader
        eyebrow="Today · antrean riset pribadi"
        title={`Selamat datang, ${profile.name}`}
        description={`Watchlist ${profile.watchlist.length} emiten · horizon ${profile.config.horizon} · urutan awal ${profile.config.pillarOrder[0]}. Data dan verdict tetap sama untuk semua profil.`}
        action={<CitationDialog citations={citations} label="Sumber hari ini" />}
      />

      <Reveal>
        <dl className="grid grid-cols-2 border-y border-border lg:grid-cols-4">
          {ledger.map((item, index) => (
            <div key={item.label} className={`px-1 py-5 sm:px-5 ${index % 2 === 0 ? "border-r border-border" : ""} lg:border-r lg:last:border-r-0 ${index < 2 ? "border-b border-border lg:border-b-0" : ""} ${index === 0 ? "sm:pl-0" : ""}`}>
              <dt className="meta text-muted-foreground">{item.label}</dt>
              <dd className="mt-3 font-mono text-[28px] font-light leading-none tabular-nums">{item.value}</dd>
              <dd className="mt-2.5 text-[12px] text-muted-foreground">{item.detail}</dd>
            </div>
          ))}
        </dl>
      </Reveal>

      <Reveal index={1} className="mt-10">
        <section aria-labelledby="ask-agent-title" className="flex flex-col gap-6 rounded-[12px] border border-border bg-surface px-6 py-7 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div className="min-w-0 max-w-xl">
            <p className="meta text-muted-foreground">Copilot</p>
            <h2 id="ask-agent-title" className="editorial mt-2.5 text-[24px]">Percepat riset lewat Copilot</h2>
            <p className="mt-2.5 text-[13.5px] leading-[1.65] text-muted-foreground">Cari alasan sebuah ticker muncul, bandingkan bukti, atau telusuri dampak berita, cuaca, dan kebijakan.</p>
          </div>
          <Link href="/copilot" className="inline-flex min-h-11 shrink-0 cursor-pointer items-center justify-center gap-2 rounded-[6px] bg-primary px-5 text-[13px] font-medium text-primary-foreground transition-[background-color,transform] duration-200 hover:bg-primary/88 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
            <IconCopilot className="size-4" />
            Tanya agent
            <IconArrowRight className="size-4" />
          </Link>
        </section>
      </Reveal>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(300px,0.85fr)]">
        <Reveal>
          <Panel className="h-full">
            <PanelHeader
              eyebrow="Watchlist · prioritas review"
              title="Kasus yang perlu dibaca"
              action={<Link href="/companies" className="inline-flex min-h-9 shrink-0 cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-[6px] px-2 text-[12px] font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Semua emiten<IconArrowRight className="size-3.5" /></Link>}
            />
            <div className="divide-y divide-border">
              {cases.map((analysis, index) => (
                <Link
                  key={analysis.company.symbol}
                  href={`/companies/${analysis.company.symbol}`}
                  className="group grid min-h-24 cursor-pointer gap-3 px-5 py-4 transition-colors hover:bg-muted/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring sm:grid-cols-[28px_minmax(0,1fr)_auto] sm:items-center sm:gap-5"
                >
                  <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                  <span className="min-w-0">
                    <span className="flex flex-wrap items-baseline gap-2.5">
                      <span className="font-mono text-[14px] font-medium">{analysis.company.symbol}</span>
                      <span className="text-[12px] text-muted-foreground">{analysis.company.name}</span>
                    </span>
                    <span className="mt-1.5 line-clamp-2 block text-[12.5px] leading-[1.6] text-muted-foreground">{analysis.thesis}</span>
                  </span>
                  <span className="flex items-center gap-3 sm:block sm:text-right">
                    <StatusBadge status={analysis.evidenceState} />
                    <span className="meta mt-2 block text-muted-foreground">{analysis.pillars[0].label} first</span>
                  </span>
                </Link>
              ))}
              {cases.length === 0 ? <p className="px-5 py-12 text-center text-[13px] text-muted-foreground">{dataset.error ?? "Watchlist belum memuat simbol yang punya kartu lengkap."}</p> : null}
            </div>
          </Panel>
        </Reveal>

        <Reveal index={1}>
          <Panel className="h-full">
            <PanelHeader eyebrow="Cakupan sumber" title="Apa yang ada di tangan" />
            <dl className="grid grid-cols-2">
              {[
                { label: "IHSG terakhir", value: latestIhsg?.ihsg ? formatNumber(latestIhsg.ihsg) : "—", note: latestIhsg?.date ?? "index-daily", tone: "muted" as const },
                { label: "Emiten dilayani", value: String(companies.length), note: `${Object.keys(analyses).length} punya kartu`, tone: "muted" as const },
                { label: "Ambang dipakai", value: String(thresholds.length), note: `${learned} learned · ${thresholds.length - learned} shipped`, tone: "muted" as const },
                { label: "Pilar menyala", value: String(flagged.length), note: "sedikitnya satu bahaya", tone: flagged.length ? "attention" as const : "positive" as const },
              ].map((item, index) => (
                <div key={item.label} className={`px-5 py-4 ${index % 2 === 0 ? "border-r border-border" : ""} ${index < 2 ? "border-b border-border" : ""}`}>
                  <dt className="text-[11px] text-muted-foreground">{item.label}</dt>
                  <dd className="mt-2 font-mono text-[19px] font-light tabular-nums">{item.value}</dd>
                  <dd className={`mt-1.5 text-[11px] ${item.tone === "positive" ? "text-positive" : item.tone === "attention" ? "text-attention" : "text-muted-foreground"}`}>{item.note}</dd>
                </div>
              ))}
            </dl>
            <div className="border-t border-border px-5 py-5">
              <p className="text-[12px] leading-[1.65] text-muted-foreground">Hitungan, bukan skor. Tidak ada angka di panel ini yang digabung menjadi satu nilai daya tarik, dan tidak ada yang dihitung di peramban.</p>
              <p className="meta mt-4 text-muted-foreground">{asOf ? `${formatAsOf(asOf)} WIB` : "belum ada kartu"}</p>
            </div>
          </Panel>
        </Reveal>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <Reveal>
          <Panel className="h-full">
            <PanelHeader
              eyebrow="Penanda verdict"
              title="Yang membuat sebuah kartu berbunyi"
              action={<Link href="/impact" className="inline-flex min-h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-[6px] px-2 text-[12px] font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Buka jalur bukti<IconArrowRight className="size-3.5" /></Link>}
            />
            {markers.length ? (
              <div className="cascade grid gap-px bg-border md:grid-cols-2">
                {markers.map((analysis) => (
                  <Link key={analysis.company.symbol} href={`/companies/${analysis.company.symbol}`} className="cursor-pointer bg-surface px-5 py-4 transition-colors hover:bg-muted/45 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
                    <span className="flex items-center justify-between gap-2">
                      <span className="meta font-mono text-muted-foreground">{analysis.company.symbol}</span>
                      <span className="meta text-muted-foreground opacity-70">{analysis.asOf}</span>
                    </span>
                    <h3 className="mt-2.5 text-[13px] font-medium leading-[1.5]">{analysis.verdict}</h3>
                    <span className="mt-3.5 flex flex-wrap gap-1.5">
                      {analysis.modifiers.map((modifier) => (
                        <span key={modifier} className="rounded-full bg-muted px-2 py-0.5 font-mono text-[10px] text-muted-foreground">{modifier}</span>
                      ))}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="px-5 py-12 text-center text-[13px] text-muted-foreground">Tidak ada kartu di watchlist yang membawa penanda tambahan. Verdict tetap dapat berbunyi tanpa penanda.</p>
            )}
          </Panel>
        </Reveal>

        <Reveal index={1}>
          <Panel className="h-full">
            <PanelHeader eyebrow="Agent health" title="Semua gate aktif" />
            <ul className="divide-y divide-border">
              {[
                { label: "Citation gate", detail: `${formatNumber(new Set(citations.map((item) => item.id)).size)} sumber unik`, icon: IconSource },
                { label: "Kartu dinilai", detail: `${Object.keys(analyses).length} dari ${companies.length} simbol`, icon: IconWatch },
                { label: "Language gate", detail: "advisory diblokir", icon: IconGate },
                { label: "Planner", detail: `${cases[0]?.hypotheses.length ?? 4} hipotesis per kartu`, icon: IconCopilot },
              ].map((item) => (
                <li key={item.label} className="flex items-center gap-3.5 px-5 py-3.5">
                  <item.icon className="size-4 shrink-0 text-muted-foreground" />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[13px] font-medium">{item.label}</span>
                    <span className="meta mt-1 block text-muted-foreground">{item.detail}</span>
                  </span>
                  <IconSignal className="size-3.5 shrink-0 text-positive" />
                </li>
              ))}
            </ul>
          </Panel>
        </Reveal>
      </div>
    </div>
  );
}
