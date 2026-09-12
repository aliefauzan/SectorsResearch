"use client";

import { demoProfiles } from "@/lib/profiles";
import { useCatalystStore } from "@/lib/store";
import type { AnswerDepth, Horizon, PillarKey } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { IconArrowDown, IconArrowUp, IconCheck, IconGate, IconSliders, IconToggleOff, IconToggleOn, IconTrash, IconUndo, IconWatch } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const pillarLabels: Record<PillarKey, string> = { concentration: "Konsentrasi", volume: "Volume", momentum: "Momentum", catalyst: "Katalis" };
const horizonLabels: Record<Horizon, string> = { event: "Event · 1-3 hari", swing: "Swing · 1-4 minggu", position: "Position · 1-3 bulan" };
const depthLabels: Record<AnswerDepth, string> = { compact: "Ringkas", standard: "Standar", forensic: "Forensik" };

const choiceClass = (selected: boolean) => cn(
  "min-h-11 w-full cursor-pointer rounded-[6px] border px-3.5 text-left text-[13px] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
  selected ? "border-foreground bg-muted font-medium text-foreground" : "border-border text-muted-foreground hover:border-foreground/30 hover:text-foreground",
);

export default function AgentPage() {
  const { profile, preferences, feedback, insights, setDemoProfile, setHorizon, setDepth, setPillarOrder, togglePreference, setInsightStatus, removeInsight, resetMemory } = useCatalystStore();
  const move = (index: number, direction: -1 | 1) => {
    const next = [...profile.config.pillarOrder];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setPillarOrder(next);
  };
  const confirmReset = () => { if (window.confirm("Hapus semua feedback dan kembalikan preferensi awal?")) resetMemory(); };

  return (
    <div className="mx-auto max-w-[1180px]">
      <PageHeader eyebrow="Agent studio" title="Atur prioritas, bukan kebenaran" description="Konfigurasi mengubah ranking, urutan, kedalaman, dan quick prompt. Kalkulator, sumber, ambang, konflik, dan language gate tidak berubah." />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(300px,0.75fr)]">
        <div className="space-y-6">
          <Reveal>
            <Panel>
              <PanelHeader eyebrow="Human review queue" title={`${insights.filter((item) => item.status === "pending").length} hipotesis menunggu verifikasi`} />
              {insights.length ? (
                <div className="divide-y divide-border">
                  {insights.map((insight) => (
                    <article key={insight.id} className="px-5 py-5">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[12px] font-medium">{insight.symbol}</span>
                        <span className="rounded-full bg-muted px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.07em] text-muted-foreground">{insight.pillar ?? "general"}</span>
                        <span className="rounded-full bg-attention-soft px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.07em] text-attention">{insight.status}</span>
                      </div>
                      <p className="mt-3 text-[13px] leading-[1.65]">{insight.note}</p>
                      <p className="mt-2 text-[11.5px] text-muted-foreground">Catatan user · belum menjadi bukti pasar</p>
                      <div className="mt-4 flex flex-wrap items-center gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setInsightStatus(insight.id, insight.status === "pending" ? "incorporated" : "pending")}>
                          {insight.status === "pending" ? "Tandai sudah diperiksa" : "Kembalikan ke antrean"}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => setInsightStatus(insight.id, "dismissed")} disabled={insight.status === "dismissed"}>Abaikan</Button>
                        <Button variant="ghost" size="icon" onClick={() => removeInsight(insight.id)} aria-label={`Hapus catatan ${insight.symbol}`} className="ml-auto text-danger hover:text-danger"><IconTrash className="size-4" /></Button>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="px-6 py-10 text-center text-[13px] leading-[1.65] text-muted-foreground">Belum ada koreksi. Tambahkan komentar dari halaman analisis perusahaan.</p>
              )}
            </Panel>
          </Reveal>

          <Reveal index={1}>
            <Panel>
              <PanelHeader eyebrow="Demo profiles" title="Bandingkan dua cara membaca" />
              <div className="grid gap-px bg-border sm:grid-cols-2">
                {demoProfiles.map((item) => (
                  <button key={item.id} onClick={() => setDemoProfile(item.id)} aria-pressed={profile.id === item.id} className={cn("min-h-32 cursor-pointer bg-surface px-5 py-5 text-left transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring", profile.id === item.id ? "bg-muted" : "hover:bg-muted/45")}>
                    <span className="flex items-center justify-between gap-3">
                      <span className="editorial text-[19px]">{item.name}</span>
                      {profile.id === item.id ? <IconCheck className="size-4" /> : null}
                    </span>
                    <span className="mt-2.5 block text-[12.5px] leading-[1.65] text-muted-foreground">{item.description}</span>
                    <span className="meta mt-4 block text-muted-foreground">{pillarLabels[item.config.pillarOrder[0]]} first</span>
                  </button>
                ))}
              </div>
              <p className="flex items-start gap-2.5 border-t border-border px-5 py-3.5 text-[12px] leading-[1.6] text-muted-foreground">
                <IconWatch className="mt-0.5 size-3.5 shrink-0" />
                Buka ANTM dengan kedua profil. Nilai metrik dan verdict sama; urutan empat pilar berubah.
              </p>
            </Panel>
          </Reveal>

          <Reveal index={2}>
            <Panel>
              <PanelHeader eyebrow="Evidence order" title="Urutan empat pilar" />
              <ol className="divide-y divide-border">
                {profile.config.pillarOrder.map((pillar, index) => (
                  <li key={pillar} className="flex items-center gap-4 px-5 py-2.5">
                    <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                    <span className="flex-1 text-[13px] font-medium">{pillarLabels[pillar]}</span>
                    <Button variant="ghost" size="icon" disabled={index === 0} onClick={() => move(index, -1)} aria-label={`Naikkan ${pillarLabels[pillar]}`}><IconArrowUp className="size-4" /></Button>
                    <Button variant="ghost" size="icon" disabled={index === 3} onClick={() => move(index, 1)} aria-label={`Turunkan ${pillarLabels[pillar]}`}><IconArrowDown className="size-4" /></Button>
                  </li>
                ))}
              </ol>
            </Panel>
          </Reveal>

          <Reveal index={3}>
            <Panel>
              <PanelHeader eyebrow="Response controls" title="Horizon dan kedalaman" />
              <div className="grid gap-6 px-5 py-5 sm:grid-cols-2">
                <fieldset>
                  <legend className="meta mb-3 text-muted-foreground">Horizon</legend>
                  <div className="space-y-2">
                    {(Object.keys(horizonLabels) as Horizon[]).map((item) => (
                      <button key={item} onClick={() => setHorizon(item)} aria-pressed={profile.config.horizon === item} className={choiceClass(profile.config.horizon === item)}>{horizonLabels[item]}</button>
                    ))}
                  </div>
                </fieldset>
                <fieldset>
                  <legend className="meta mb-3 text-muted-foreground">Kedalaman</legend>
                  <div className="space-y-2">
                    {(Object.keys(depthLabels) as AnswerDepth[]).map((item) => (
                      <button key={item} onClick={() => setDepth(item)} aria-pressed={profile.config.depth === item} className={choiceClass(profile.config.depth === item)}>{depthLabels[item]}</button>
                    ))}
                  </div>
                </fieldset>
              </div>
            </Panel>
          </Reveal>
        </div>

        <div className="space-y-6">
          <Reveal>
            <Panel>
              <PanelHeader eyebrow="Learned memory" title={`${preferences.filter((item) => item.active).length} preferensi aktif`} />
              <div className="divide-y divide-border">
                {preferences.map((item) => (
                  <div key={item.id} className="flex gap-3 px-4 py-4">
                    <button onClick={() => togglePreference(item.id)} aria-pressed={item.active} aria-label={`${item.active ? "Matikan" : "Aktifkan"} ${item.label}`} className="grid size-10 shrink-0 cursor-pointer place-items-center rounded-[6px] transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                      {item.active ? <IconToggleOn className="size-5" /> : <IconToggleOff className="size-5 text-muted-foreground" />}
                    </button>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-[13px] font-medium">{item.label}</p>
                        <span className="rounded-full bg-muted px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.07em] text-muted-foreground">{item.source}</span>
                      </div>
                      <p className="mt-1.5 text-[12px] leading-[1.6] text-muted-foreground">{item.explanation}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="border-t border-border px-5 py-5">
                <Button variant="danger" className="w-full" onClick={confirmReset}><IconUndo className="size-4" />Reset memori</Button>
                <p className="meta mt-3 text-center text-muted-foreground">{feedback.length} feedback · {insights.length} catatan · lokal</p>
              </div>
            </Panel>
          </Reveal>

          <Reveal index={1}>
            <Panel>
              <PanelHeader eyebrow="Immutable gates" title="Tidak dapat dilatih ulang" />
              <ul className="divide-y divide-border">
                {["Angka dan formula", "Metadata citation", "Ambang analisis", "Status kontradiksi", "Pembatas bahasa"].map((item) => (
                  <li key={item} className="flex items-center gap-3 px-5 py-3 text-[13px]">
                    <IconGate className="size-3.5 shrink-0 text-positive" />{item}
                  </li>
                ))}
              </ul>
            </Panel>
          </Reveal>

          <Reveal index={2}>
            <Panel className="px-5 py-5">
              <div className="flex gap-3.5">
                <IconSliders className="mt-1 size-4 shrink-0 text-muted-foreground" />
                <div>
                  <h2 className="editorial text-[17px]">Yang berubah sekarang</h2>
                  <p className="mt-2 text-[12.5px] leading-[1.7] text-muted-foreground">{pillarLabels[profile.config.pillarOrder[0]]} tampil pertama, horizon {horizonLabels[profile.config.horizon].toLowerCase()}, jawaban {depthLabels[profile.config.depth].toLowerCase()}.</p>
                </div>
              </div>
            </Panel>
          </Reveal>
        </div>
      </div>
    </div>
  );
}
