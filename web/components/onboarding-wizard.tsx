"use client";

import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useDataset } from "@/lib/dataset";
import { useCatalystStore } from "@/lib/store";
import type { AnswerDepth, Horizon, PillarKey, SymbolCode } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { IconArrowDown, IconArrowLeft, IconArrowRight, IconArrowUp, IconCheck, IconSeal, IconSource, IconUndo, IconWatch } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const pillarLabels: Record<PillarKey, string> = { concentration: "Konsentrasi", volume: "Volume", momentum: "Momentum", catalyst: "Katalis" };
const horizons: Array<{ id: Horizon; label: string; detail: string }> = [
  { id: "event", label: "Event", detail: "1-3 hari" },
  { id: "swing", label: "Swing", detail: "1-4 minggu" },
  { id: "position", label: "Position", detail: "1-3 bulan" },
];
const depths: Array<{ id: AnswerDepth; label: string; detail: string }> = [
  { id: "compact", label: "Ringkas", detail: "Verdict dan bukti utama" },
  { id: "standard", label: "Standar", detail: "Metrik, konflik, dan sumber" },
  { id: "forensic", label: "Forensik", detail: "Trace serta detail field" },
];
const stepTitles = ["Semesta riset", "Jendela analisis", "Urutan dan kedalaman", "Batas agent"];

const selectableClass = (selected: boolean) => cn(
  "cursor-pointer rounded-[8px] border text-left transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
  selected ? "border-foreground bg-muted" : "border-border hover:border-foreground/30 hover:bg-muted/50",
);

export function OnboardingWizard() {
  const { companies } = useDataset();
  const [step, setStep] = useState(1);
  const { profile, setWatchlist, toggleOwned, setHorizon, setDepth, setPillarOrder, completeOnboarding } = useCatalystStore();
  const movePillar = (index: number, direction: -1 | 1) => {
    const next = [...profile.config.pillarOrder];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setPillarOrder(next);
  };
  const toggleTicker = (symbol: SymbolCode) => {
    if (profile.watchlist.includes(symbol)) {
      if (profile.watchlist.length <= 5) return;
      setWatchlist(profile.watchlist.filter((item) => item !== symbol));
    } else if (profile.watchlist.length < 15) setWatchlist([...profile.watchlist, symbol]);
  };

  return (
    <Dialog.Root open={!profile.hasOnboarded}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-100 bg-[#14130f]/85 backdrop-blur-md" />
        <Dialog.Content
          onEscapeKeyDown={(event) => event.preventDefault()}
          onPointerDownOutside={(event) => event.preventDefault()}
          className="fixed inset-x-3 top-1/2 z-100 mx-auto max-h-[92dvh] w-auto max-w-3xl -translate-y-1/2 overflow-y-auto rounded-[12px] border border-border bg-surface shadow-overlay focus:outline-none sm:inset-x-6"
        >
          <div className="border-b border-border px-6 py-6 sm:px-8">
            <div className="flex items-start justify-between gap-6">
              <div className="min-w-0">
                <p className="meta text-muted-foreground">Setup agent · langkah {step} dari 4</p>
                <Dialog.Title className="editorial mt-2.5 text-[27px]">Atur cara Catalyst bekerja</Dialog.Title>
              </div>
              <span className="meta shrink-0 text-muted-foreground">catalyst:v1</span>
            </div>
            <ol className="mt-6 grid grid-cols-4 gap-3" aria-label={`Langkah ${step} dari 4`}>
              {stepTitles.map((title, index) => (
                <li key={title}>
                  <span className={cn("block h-px w-full", index < step ? "bg-foreground" : "bg-border")} />
                  <span className={cn("meta mt-2 hidden truncate sm:block", index < step ? "text-foreground" : "text-muted-foreground")}>{title}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="min-h-[400px] px-6 py-7 sm:px-8">
            {step === 1 ? (
              <div>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="max-w-xl">
                    <h2 className="editorial text-[21px]">Pilih semesta riset</h2>
                    <p className="mt-2 text-[13px] leading-[1.65] text-muted-foreground">Pilih 5-15 ticker. Penanda dimiliki tidak meminta lot, harga perolehan, atau nilai investasi.</p>
                  </div>
                  <span className="rounded-full bg-muted px-3 py-1.5 font-mono text-[11px] tabular-nums text-muted-foreground">{profile.watchlist.length}/15 dipilih</span>
                </div>
                <div className="mt-6 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {companies.map((company) => {
                    const selected = profile.watchlist.includes(company.symbol);
                    const owned = profile.owned.includes(company.symbol);
                    return (
                      <div key={company.symbol} className={cn(selectableClass(selected), "p-3")}>
                        <button onClick={() => toggleTicker(company.symbol)} aria-pressed={selected} className="flex min-h-11 w-full cursor-pointer items-center gap-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                          <span className={cn("grid size-4.5 shrink-0 place-items-center rounded-[4px] border", selected ? "border-foreground bg-foreground text-background" : "border-border")}>
                            {selected ? <IconCheck className="size-3" /> : null}
                          </span>
                          <span className="min-w-0">
                            <span className="block font-mono text-[13px] font-medium">{company.symbol}</span>
                            <span className="block truncate text-[11px] text-muted-foreground">{company.subsector}</span>
                          </span>
                        </button>
                        {selected ? (
                          <button onClick={() => toggleOwned(company.symbol)} aria-pressed={owned} className={cn("mt-2.5 min-h-8 w-full cursor-pointer rounded-[4px] border px-2 text-[11px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", owned ? "border-transparent bg-attention-soft text-attention" : "border-border text-muted-foreground hover:bg-muted")}>
                            {owned ? "Dimiliki" : "Tandai dimiliki"}
                          </button>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {step === 2 ? (
              <div>
                <h2 className="editorial text-[21px]">Pilih jendela analisis</h2>
                <p className="mt-2 max-w-xl text-[13px] leading-[1.65] text-muted-foreground">Horizon mengubah prioritas event dan panjang baseline yang dijelaskan, bukan rumus inti.</p>
                <div className="mt-7 grid gap-3 sm:grid-cols-3">
                  {horizons.map((item) => (
                    <button key={item.id} onClick={() => setHorizon(item.id)} aria-pressed={profile.config.horizon === item.id} className={cn(selectableClass(profile.config.horizon === item.id), "min-h-28 p-5")}>
                      <span className="editorial block text-[19px]">{item.label}</span>
                      <span className="mt-2.5 block font-mono text-[12px] text-muted-foreground">{item.detail}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="grid gap-10 md:grid-cols-2">
                <div>
                  <h2 className="editorial text-[21px]">Urutkan empat pilar</h2>
                  <p className="mt-2 text-[13px] leading-[1.65] text-muted-foreground">Urutan mengatur penyajian. Verdict tetap dihitung dari bukti yang sama.</p>
                  <ol className="mt-5 divide-y divide-border border-y border-border">
                    {profile.config.pillarOrder.map((pillar, index) => (
                      <li key={pillar} className="flex items-center gap-3 py-2.5">
                        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                        <span className="flex-1 text-[13px] font-medium">{pillarLabels[pillar]}</span>
                        <Button variant="ghost" size="icon" disabled={index === 0} onClick={() => movePillar(index, -1)} aria-label={`Naikkan ${pillarLabels[pillar]}`}><IconArrowUp className="size-4" /></Button>
                        <Button variant="ghost" size="icon" disabled={index === 3} onClick={() => movePillar(index, 1)} aria-label={`Turunkan ${pillarLabels[pillar]}`}><IconArrowDown className="size-4" /></Button>
                      </li>
                    ))}
                  </ol>
                </div>
                <div>
                  <h2 className="editorial text-[21px]">Kedalaman jawaban</h2>
                  <p className="mt-2 text-[13px] leading-[1.65] text-muted-foreground">Mengatur berapa banyak lapisan bukti yang dibuka lebih dulu.</p>
                  <div className="mt-5 space-y-2">
                    {depths.map((item) => (
                      <button key={item.id} onClick={() => setDepth(item.id)} aria-pressed={profile.config.depth === item.id} className={cn(selectableClass(profile.config.depth === item.id), "min-h-16 w-full px-4 py-3")}>
                        <span className="block text-[13px] font-medium">{item.label}</span>
                        <span className="mt-0.5 block text-[12px] text-muted-foreground">{item.detail}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {step === 4 ? (
              <div>
                <h2 className="editorial text-[21px]">Batas agent</h2>
                <p className="mt-2 max-w-xl text-[13px] leading-[1.65] text-muted-foreground">Tiga aturan ini selalu aktif dan tidak dapat dilatih ulang oleh feedback.</p>
                <div className="mt-7 grid gap-px border border-border bg-border sm:grid-cols-3">
                  {[
                    { icon: IconSource, title: "Fakta tetap", text: "Feedback tidak mengubah angka, sumber, rumus, ambang, atau status konflik." },
                    { icon: IconWatch, title: "Memori terlihat", text: "Preferensi yang dipelajari dapat dilihat, dimatikan, atau dihapus." },
                    { icon: IconUndo, title: "Fail closed", text: "Pertanyaan tanpa kartu pendukung berhenti pada bukti yang belum cukup." },
                  ].map((item) => (
                    <div key={item.title} className="bg-surface p-5">
                      <item.icon className="size-4.5 text-muted-foreground" />
                      <h3 className="mt-4 text-[13px] font-medium">{item.title}</h3>
                      <p className="mt-2 text-[12.5px] leading-[1.65] text-muted-foreground">{item.text}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-6 flex gap-3 rounded-[8px] bg-muted p-4 text-[13px] leading-[1.7]">
                  <IconSeal className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  <span>
                    Agent akan memakai profil <strong className="font-medium">{profile.name}</strong>, horizon <strong className="font-medium">{horizons.find((item) => item.id === profile.config.horizon)?.detail}</strong>, dan kedalaman <strong className="font-medium">{depths.find((item) => item.id === profile.config.depth)?.label}</strong>.
                  </span>
                </p>
              </div>
            ) : null}
          </div>

          <div className="flex items-center justify-between gap-4 border-t border-border px-6 py-5 sm:px-8">
            <Button variant="ghost" onClick={() => setStep((value) => Math.max(1, value - 1))} disabled={step === 1}><IconArrowLeft className="size-4" />Kembali</Button>
            {step < 4
              ? <Button onClick={() => setStep((value) => Math.min(4, value + 1))}>Lanjut<IconArrowRight className="size-4" /></Button>
              : <Button onClick={completeOnboarding}>Masuk ke Today<IconArrowRight className="size-4" /></Button>}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
