"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useDataset } from "@/lib/dataset";
import type { Sector } from "@/lib/types";
import { formatAsOf, formatCurrency, formatPercentChange, orDash } from "@/lib/utils";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { StatusBadge } from "@/components/ui/status-badge";
import { IconArrowUpRight, IconEmpty, IconFilter, IconSearch } from "@/components/ui/icons";

export default function CompaniesPage() {
  const { companies, source, error } = useDataset();
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState<Sector | "Semua">("Semua");
  // The sector list is whatever the company reports carried. A symbol whose report is absent
  // has no sector and is reachable only through "Semua", which is the truthful placement.
  const sectors = useMemo(
    () => ["Semua", ...[...new Set(companies.map((company) => company.sector).filter((item): item is string => Boolean(item)))].sort()] as Array<Sector | "Semua">,
    [companies],
  );
  const analyzed = companies.filter((company) => company.analyzed).length;
  const filtered = useMemo(() => companies.filter((company) =>
    (sector === "Semua" || company.sector === sector) &&
    `${company.symbol} ${company.name ?? ""} ${company.subsector ?? ""}`.toLowerCase().includes(query.toLowerCase()),
  ), [companies, query, sector]);

  return (
    <div className="mx-auto max-w-[1180px]">
      <PageHeader
        eyebrow={`Company universe · sumber ${source || "—"}`}
        title={`${companies.length} emiten dilayani`}
        description={`${analyzed} di antaranya punya kartu empat pilar lengkap. Sisanya tetap dapat dibuka: halaman menampilkan alasan penolakannya apa adanya, bukan angka pengganti.`}
      />

      {error ? (
        <Panel className="mb-6 px-6 py-8 text-center">
          <IconEmpty className="mx-auto size-6 text-muted-foreground" />
          <h2 className="editorial mt-4 text-[19px]">Data tidak dapat diambil</h2>
          <p className="mt-2 text-[13px] text-muted-foreground">{error}</p>
        </Panel>
      ) : null}

      <div className="mb-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_260px]">
        <label className="relative block">
          <span className="sr-only">Cari emiten</span>
          <IconSearch className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Cari ticker, nama, atau subsektor" className="h-11 w-full rounded-[6px] border border-border bg-surface pl-10 pr-3 text-[14px] outline-none transition-colors placeholder:text-muted-foreground focus:border-foreground/40 focus:ring-2 focus:ring-ring/25" />
        </label>
        <label className="relative block">
          <span className="sr-only">Filter sektor</span>
          <IconFilter className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <select value={sector} onChange={(event) => setSector(event.target.value as Sector | "Semua")} className="h-11 w-full cursor-pointer appearance-none rounded-[6px] border border-border bg-surface pl-10 pr-3 text-[13px] outline-none transition-colors focus:border-foreground/40 focus:ring-2 focus:ring-ring/25">
            {sectors.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
      </div>

      <Reveal>
        <div className="hidden overflow-hidden rounded-[12px] border border-border bg-surface md:block">
          <table className="w-full text-left text-[13px]">
            <caption className="sr-only">Emiten yang dilayani sumber ini</caption>
            <thead>
              <tr className="border-b border-border">
                <th className="meta px-5 py-3.5 font-normal text-muted-foreground">Emiten</th>
                <th className="meta px-4 py-3.5 font-normal text-muted-foreground">Sektor</th>
                <th className="meta px-4 py-3.5 text-right font-normal text-muted-foreground">Harga</th>
                <th className="meta px-4 py-3.5 text-right font-normal text-muted-foreground">Gerak</th>
                <th className="meta px-4 py-3.5 font-normal text-muted-foreground">Status bukti</th>
                <th className="px-5 py-3.5"><span className="sr-only">Buka</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((company) => (
                <tr key={company.symbol} className="transition-colors hover:bg-muted/45">
                  <td className="px-5 py-3.5">
                    <Link href={`/companies/${company.symbol}`} className="inline-flex min-h-10 items-center gap-4 rounded-[4px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                      <span className="font-mono text-[13px] font-medium">{company.symbol}</span>
                      <span>
                        <span className="block text-[13px]">{orDash(company.name)}</span>
                        <span className="block text-[11px] text-muted-foreground">{orDash(company.subsector)}</span>
                      </span>
                    </Link>
                  </td>
                  <td className="px-4 py-3.5 text-[12px] text-muted-foreground">{orDash(company.sector)}</td>
                  <td className="px-4 py-3.5 text-right font-mono tabular-nums">{company.price === null ? "—" : formatCurrency(company.price)}</td>
                  <td className={`px-4 py-3.5 text-right font-mono tabular-nums ${company.changePct === null ? "text-muted-foreground" : company.changePct >= 0 ? "text-positive" : "text-danger"}`}>{formatPercentChange(company.changePct)}</td>
                  <td className="px-4 py-3.5"><StatusBadge status={company.evidenceState} /></td>
                  <td className="px-5 py-3.5 text-right">
                    <Link href={`/companies/${company.symbol}`} aria-label={`Buka ${company.symbol}`} className="inline-grid size-10 place-items-center rounded-[6px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                      <IconArrowUpRight className="size-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Reveal>

      <div className="grid gap-3 md:hidden">
        {filtered.map((company) => (
          <Link key={company.symbol} href={`/companies/${company.symbol}`} className="cursor-pointer rounded-[12px] border border-border bg-surface p-5 transition-colors hover:border-foreground/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <span className="flex items-start justify-between gap-3">
              <span className="min-w-0">
                <span className="font-mono text-[13px] font-medium">{company.symbol}</span>
                <h2 className="mt-1.5 text-[14px] font-medium">{orDash(company.name)}</h2>
                <span className="mt-1 block text-[11.5px] text-muted-foreground">{orDash(company.sector)} · {orDash(company.subsector)}</span>
              </span>
              <IconArrowUpRight className="size-4 shrink-0 text-muted-foreground" />
            </span>
            <span className="mt-5 flex items-end justify-between gap-3">
              <span>
                <span className="block font-mono text-[18px] font-light tabular-nums">{company.price === null ? "—" : formatCurrency(company.price)}</span>
                <span className="meta mt-1.5 block text-muted-foreground">{company.asOf ? `${formatAsOf(company.asOf)} WIB` : "—"}</span>
              </span>
              <StatusBadge status={company.evidenceState} />
            </span>
          </Link>
        ))}
      </div>

      {filtered.length === 0 ? (
        <Panel className="px-6 py-16 text-center">
          <IconEmpty className="mx-auto size-6 text-muted-foreground" />
          <h2 className="editorial mt-5 text-[21px]">Tidak ada emiten yang cocok</h2>
          <p className="mt-2 text-[13px] text-muted-foreground">Ubah kata kunci atau filter sektor.</p>
        </Panel>
      ) : null}
    </div>
  );
}
