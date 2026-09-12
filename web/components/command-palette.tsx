"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/button";
import {
  IconAgent,
  IconClose,
  IconCompanies,
  IconCopilot,
  IconImpact,
  IconMethod,
  IconSearch,
  IconToday,
} from "@/components/ui/icons";

const actions = [
  { label: "Buka Today", href: "/", icon: IconToday },
  { label: "Cari emiten", href: "/companies", icon: IconCompanies },
  { label: "Buka impact map", href: "/impact", icon: IconImpact },
  { label: "Tanya Catalyst Copilot", href: "/copilot", icon: IconCopilot },
  { label: "Atur agent", href: "/agent", icon: IconAgent },
  { label: "Baca metode", href: "/method", icon: IconMethod },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (event.key === "/" && !target?.matches("input, textarea, [contenteditable='true']")) {
        event.preventDefault();
        setOpen(true);
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const filtered = actions.filter((action) => action.label.toLowerCase().includes(query.toLowerCase()));
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="secondary" size="sm" aria-label="Buka command palette" className="hidden w-full justify-start gap-2.5 bg-background text-muted-foreground lg:flex">
          <IconSearch className="size-4" />
          <span className="font-normal">Cari atau buka</span>
          <kbd className="ml-auto">/</kbd>
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-100 bg-foreground/35 backdrop-blur-[3px]" />
        <Dialog.Content className="fixed left-1/2 top-[16vh] z-100 w-[min(92vw,560px)] -translate-x-1/2 overflow-hidden rounded-[12px] border border-border bg-surface shadow-overlay focus:outline-none">
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <div className="flex items-center gap-3 border-b border-border px-4">
            <IconSearch className="size-4 text-muted-foreground" />
            <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Cari halaman..." className="h-14 min-w-0 flex-1 bg-transparent text-[15px] outline-none placeholder:text-muted-foreground" aria-label="Cari halaman" />
            <Dialog.Close asChild><Button variant="ghost" size="icon" aria-label="Tutup command palette"><IconClose className="size-4" /></Button></Dialog.Close>
          </div>
          <div className="p-2">
            {filtered.map((action) => (
              <button key={action.href} onClick={() => { router.push(action.href); setOpen(false); }} className="flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-[6px] px-3 text-left text-[13px] transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <action.icon className="size-4 text-muted-foreground" />{action.label}
              </button>
            ))}
            {filtered.length === 0 ? <p className="p-4 text-[13px] text-muted-foreground">Tidak ada halaman yang cocok.</p> : null}
          </div>
          <div className="flex items-center gap-4 border-t border-border bg-surface-raised px-4 py-2.5">
            <span className="meta text-muted-foreground">Navigasi</span>
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground"><kbd>/</kbd> buka</span>
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground"><kbd>esc</kbd> tutup</span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
