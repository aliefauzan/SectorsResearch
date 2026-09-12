"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PricePoint } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { IconClose, IconExpand } from "@/components/ui/icons";
import { formatNumber } from "@/lib/utils";

function Chart({ data, height = 320 }: { data: PricePoint[]; height?: number }) {
  // The index has no row on every date the tape does. A missing close becomes null rather
  // than a carried-forward value, so the dashed IHSG line breaks where the data breaks
  // instead of drawing a flat segment that was never observed.
  const base = data.find((point) => point.ihsg !== null)?.ihsg ?? null;
  const normalized = data.map((point) => ({
    ...point,
    stockIndex: Number((point.close / data[0].close * 100).toFixed(2)),
    ihsgIndex: point.ihsg === null || base === null ? null : Number((point.ihsg / base * 100).toFixed(2)),
    shortDate: point.date.slice(5),
  }));
  return (
    <div style={{ height }} className="w-full" aria-label="Grafik indeks harga saham versus IHSG dan volume harian">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={normalized} margin={{ top: 12, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
          <XAxis dataKey="shortDate" tick={{ fill: "var(--muted-foreground)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={34} />
          <YAxis yAxisId="price" tick={{ fill: "var(--muted-foreground)", fontSize: 10, fontFamily: "var(--font-mono)" }} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
          <YAxis yAxisId="volume" orientation="right" hide domain={[0, "dataMax * 4"]} />
          <Tooltip
            cursor={{ stroke: "var(--border)", strokeWidth: 1 }}
            contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, boxShadow: "var(--shadow-overlay)", fontFamily: "var(--font-mono)", fontSize: 11 }}
            formatter={(value, name) => [name === "Volume" ? formatNumber(Number(value)) : `${Number(value).toFixed(2)} idx`, name]}
            labelFormatter={(value) => `Tanggal ${value}`}
          />
          <Legend wrapperStyle={{ fontSize: 10, fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.08em" }} />
          <Bar yAxisId="volume" dataKey="volume" name="Volume" fill="var(--chart-bar)" opacity={0.28} radius={[1, 1, 0, 0]} isAnimationActive={false} />
          <Line yAxisId="price" type="monotone" dataKey="stockIndex" name="Saham (indeks)" stroke="var(--chart-line)" strokeWidth={1.75} dot={false} activeDot={{ r: 3.5 }} isAnimationActive={false} />
          <Line yAxisId="price" type="monotone" dataKey="ihsgIndex" name="IHSG (indeks)" stroke="var(--muted-foreground)" strokeWidth={1.25} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PriceChart({ data, symbol }: { data: PricePoint[]; symbol: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-[12px] border border-border bg-surface">
      <div className="flex items-center justify-between gap-4 border-b border-border px-5 py-4">
        <div>
          <p className="meta text-muted-foreground">45 hari bursa · indeks 100</p>
          <h2 className="editorial mt-1.5 text-[17px]">{symbol} vs IHSG</h2>
        </div>
        <Button variant="secondary" size="sm" onClick={() => setOpen(true)}><IconExpand className="size-3.5" />Fokus chart</Button>
      </div>

      <div className="px-3 py-4"><Chart data={data} /></div>

      <details className="group border-t border-border">
        <summary className="flex min-h-11 cursor-pointer list-none items-center px-5 text-[12px] font-medium transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
          Buka tabel data alternatif
          <span aria-hidden="true" className="ml-auto font-mono text-[15px] leading-none text-muted-foreground">
            <span className="group-open:hidden">+</span>
            <span className="hidden group-open:inline">−</span>
          </span>
        </summary>
        <div className="max-h-72 overflow-auto border-t border-border">
          <table className="w-full text-left text-[11.5px]">
            <caption className="sr-only">Data harga {symbol}, IHSG, dan volume</caption>
            <thead className="sticky top-0 bg-surface">
              <tr className="border-b border-border">
                <th className="meta px-5 py-2.5 font-normal text-muted-foreground">Tanggal</th>
                <th className="meta px-3 py-2.5 text-right font-normal text-muted-foreground">Close</th>
                <th className="meta px-3 py-2.5 text-right font-normal text-muted-foreground">IHSG</th>
                <th className="meta px-5 py-2.5 text-right font-normal text-muted-foreground">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono tabular-nums">
              {data.map((point) => (
                <tr key={point.date}>
                  <td className="px-5 py-2 text-muted-foreground">{point.date}</td>
                  <td className="px-3 py-2 text-right">{formatNumber(point.close)}</td>
                  <td className="px-3 py-2 text-right">{point.ihsg === null ? "—" : formatNumber(point.ihsg)}</td>
                  <td className="px-5 py-2 text-right">{formatNumber(point.volume)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-100 bg-foreground/40 backdrop-blur-[3px]" />
          <Dialog.Content className="fixed inset-3 z-100 overflow-auto rounded-[12px] border border-border bg-surface px-5 py-5 shadow-overlay focus:outline-none sm:inset-8 sm:px-8 sm:py-7">
            <div className="mb-6 flex items-start gap-4">
              <div className="flex-1">
                <p className="meta text-muted-foreground">Fokus chart</p>
                <Dialog.Title className="editorial mt-2 text-[26px]">{symbol} vs IHSG</Dialog.Title>
                <Dialog.Description className="mt-2 text-[13px] leading-[1.65] text-muted-foreground">Indeks 100 pada awal periode. Volume memakai sumbu terpisah.</Dialog.Description>
              </div>
              <Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="Tutup chart"><IconClose className="size-4" /></Button></Dialog.Close>
            </div>
            <Chart data={data} height={520} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
