"use client";

import * as Dialog from "@radix-ui/react-dialog";
import type { Citation } from "@/lib/types";
import { formatAsOf } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { IconClose, IconExternal, IconInfo, IconSource } from "@/components/ui/icons";

export function CitationDialog({ citations, label = "Periksa sumber" }: { citations: Citation[]; label?: string }) {
  const unique = [...new Map(citations.map((citation) => [citation.id, citation])).values()];
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button variant="secondary" size="sm">
          <IconSource className="size-3.5" />
          {label}
          <span className="rounded-full bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">{unique.length}</span>
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-100 bg-foreground/35 backdrop-blur-[3px]" />
        <Dialog.Content className="fixed inset-y-0 right-0 z-100 w-[min(100vw,480px)] overflow-y-auto border-l border-border bg-surface px-6 py-7 shadow-overlay focus:outline-none sm:px-8">
          <div className="flex items-start gap-4">
            <div className="min-w-0 flex-1">
              <p className="meta text-muted-foreground">Provenance</p>
              <Dialog.Title className="editorial mt-2 text-[26px]">Ledger bukti</Dialog.Title>
              <Dialog.Description className="mt-2.5 text-[13px] leading-[1.65] text-muted-foreground">Setiap angka memakai provider, endpoint, field, dan waktu data.</Dialog.Description>
            </div>
            <Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="Tutup sumber"><IconClose className="size-4" /></Button></Dialog.Close>
          </div>

          <p className="mt-6 flex gap-2.5 rounded-[8px] bg-attention-soft p-3.5 text-[12px] leading-[1.6] text-attention">
            <IconInfo className="mt-0.5 size-3.5 shrink-0" />
            Setiap angka di bawah dihitung oleh KATALIS dari payload Sectors yang sudah direkam, bukan oleh peramban. Endpoint dan field adalah tempat angka itu benar-benar berasal; tautannya menunjuk dokumentasi API, bukan bukti bahwa sebuah peristiwa terjadi.
          </p>

          <div className="mt-8 divide-y divide-border border-t border-border">
            {unique.map((citation) => (
              <article key={citation.id} className="py-5">
                <p className="meta text-muted-foreground">{citation.provider}</p>
                <h3 className="mt-2 text-[14px] font-medium leading-[1.5]">{citation.label}</h3>
                <dl className="mt-3.5 space-y-2 text-[12px]">
                  <div className="flex gap-3">
                    <dt className="w-[68px] shrink-0 text-muted-foreground">Endpoint</dt>
                    <dd className="min-w-0 break-all font-mono">{citation.endpoint}</dd>
                  </div>
                  <div className="flex gap-3">
                    <dt className="w-[68px] shrink-0 text-muted-foreground">Field</dt>
                    <dd className="min-w-0 break-words font-mono">{citation.field}</dd>
                  </div>
                  <div className="flex gap-3">
                    <dt className="w-[68px] shrink-0 text-muted-foreground">As of</dt>
                    <dd className="min-w-0 font-mono">{formatAsOf(citation.asOf)} WIB</dd>
                  </div>
                </dl>
                {citation.url ? (
                  <a href={citation.url} target="_blank" rel="noreferrer" className="mt-4 inline-flex min-h-9 cursor-pointer items-center gap-2 rounded-[6px] border border-border px-3 text-[12px] font-medium transition-colors hover:border-foreground/30 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                    <IconExternal className="size-3.5" />
                    {citation.urlLabel ?? "Buka sumber"}
                    <span className="sr-only"> di tab baru</span>
                  </a>
                ) : null}
              </article>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
