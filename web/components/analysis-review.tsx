"use client";

import { FormEvent, useState } from "react";
import { useCatalystStore } from "@/lib/store";
import type { PillarKey, SymbolCode, UserInsight } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { IconGate, IconNote, IconVerified } from "@/components/ui/icons";

const categoryLabels: Record<UserInsight["category"], string> = {
  "data-error": "Data terlihat keliru",
  "missing-context": "Konteks belum masuk",
  "alternative-interpretation": "Interpretasi alternatif",
};

const pillarLabels: Record<PillarKey, string> = {
  concentration: "Konsentrasi",
  volume: "Volume",
  momentum: "Momentum",
  catalyst: "Katalis",
};

const fieldClass = "mt-2 h-11 w-full cursor-pointer rounded-[6px] border border-border bg-background px-3 text-[13px] outline-none transition-colors focus:border-foreground/40 focus:ring-2 focus:ring-ring/25";

export function AnalysisReview({ symbol }: { symbol: SymbolCode }) {
  const { insights, recordInsight } = useCatalystStore();
  const [note, setNote] = useState("");
  const [category, setCategory] = useState<UserInsight["category"]>("missing-context");
  const [pillar, setPillar] = useState<PillarKey>("catalyst");
  const [touched, setTouched] = useState(false);
  const [saved, setSaved] = useState(false);
  const error = touched && note.trim().length < 8 ? "Jelaskan koreksi sedikitnya 8 karakter agar dapat diuji." : "";
  const symbolInsights = insights.filter((insight) => insight.symbol === symbol);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setTouched(true);
    if (note.trim().length < 8) return;
    recordInsight({ symbol, pillar, category, note: note.trim() });
    setNote("");
    setTouched(false);
    setSaved(true);
  };

  return (
    <Panel>
      <PanelHeader eyebrow="Human-in-the-loop" title="Koreksi analisis ini" />
      <div className="px-5 py-5">
        <p className="flex gap-2.5 rounded-[8px] bg-muted p-3.5 text-[12px] leading-[1.6] text-muted-foreground">
          <IconGate className="mt-0.5 size-3.5 shrink-0 text-foreground" />
          Catatan Anda menjadi hipotesis terbuka. Agent boleh mengubah urutan pemeriksaan, tetapi tidak mengubah angka, rumus, sumber, atau verdict sebelum verifikasi.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-[12px] font-medium">
              Jenis masukan
              <select value={category} onChange={(event) => setCategory(event.target.value as UserInsight["category"])} className={fieldClass}>
                {(Object.keys(categoryLabels) as UserInsight["category"][]).map((item) => <option key={item} value={item}>{categoryLabels[item]}</option>)}
              </select>
            </label>
            <label className="block text-[12px] font-medium">
              Pilar terkait
              <select value={pillar} onChange={(event) => setPillar(event.target.value as PillarKey)} className={fieldClass}>
                {(Object.keys(pillarLabels) as PillarKey[]).map((item) => <option key={item} value={item}>{pillarLabels[item]}</option>)}
              </select>
            </label>
          </div>

          <div>
            <label htmlFor={`analysis-note-${symbol}`} className="block text-[12px] font-medium">Apa yang keliru atau belum dipertimbangkan?</label>
            <textarea
              id={`analysis-note-${symbol}`}
              maxLength={800}
              value={note}
              onChange={(event) => { setNote(event.target.value); setSaved(false); }}
              onBlur={() => setTouched(true)}
              aria-describedby={`analysis-note-help-${symbol} ${error ? `analysis-note-error-${symbol}` : ""}`}
              rows={4}
              placeholder="Contoh: jalur rupiah belum membedakan kontrak dalam USD dan IDR..."
              className="mt-2 w-full resize-y rounded-[6px] border border-border bg-background px-3 py-2.5 text-[13.5px] leading-[1.65] outline-none transition-colors placeholder:text-muted-foreground focus:border-foreground/40 focus:ring-2 focus:ring-ring/25"
            />
          </div>

          <div id={`analysis-note-help-${symbol}`} className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
            <span>Maksimum 800 karakter · tersimpan lokal</span>
            <span className="font-mono tabular-nums">{note.length}/800</span>
          </div>
          {error ? <p id={`analysis-note-error-${symbol}`} role="alert" className="text-[12px] text-danger">{error}</p> : null}

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button type="submit" disabled={note.trim().length < 8}><IconNote className="size-4" />Kirim untuk verifikasi</Button>
            {saved ? <p role="status" className="inline-flex items-center gap-1.5 text-[12px] text-positive"><IconVerified className="size-4" />Tersimpan sebagai hipotesis terbuka</p> : null}
          </div>
        </form>

        {symbolInsights.length ? (
          <div className="mt-7 border-t border-border pt-5">
            <p className="meta text-muted-foreground">{symbolInsights.length} catatan pada {symbol}</p>
            <div className="mt-3 divide-y divide-border">
              {symbolInsights.slice(0, 2).map((insight) => (
                <article key={insight.id} className="py-3.5 first:pt-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-attention-soft px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.07em] text-attention">{insight.status}</span>
                    <span className="text-[11px] text-muted-foreground">{pillarLabels[insight.pillar ?? "catalyst"]}</span>
                  </div>
                  <p className="mt-2 text-[12.5px] leading-[1.6]">{insight.note}</p>
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
