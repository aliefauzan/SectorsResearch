"use client";

import { FormEvent, useState } from "react";
import { useCatalystStore } from "@/lib/store";
import type { ChatAnswer } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { CitationDialog } from "@/components/citation-dialog";
import { IconCaretDown, IconClose, IconCopilot, IconExternal, IconGate, IconSend, IconUser } from "@/components/ui/icons";

const prompts = [
  "Kenapa LIFE masuk daftar?",
  "Apa yang dikatakan pilar katalis?",
  "Bandingkan LIFE dan BBCA.",
  "Data apa yang belum diperiksa?",
];

interface Message { id: string; role: "user" | "assistant"; text: string; answer?: ChatAnswer }

export function Copilot({ dismissible = false, workspace = false }: { dismissible?: boolean; workspace?: boolean }) {
  const { profile, insights, setCopilotOpen } = useCatalystStore();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { id: "intro", role: "assistant", text: `Saya membaca kartu KATALIS dengan urutan ${profile.config.pillarOrder.join(" → ")}. Tanyakan satu ticker, bandingkan dua, atau tanyakan apa yang belum diperiksa. Saya tidak menghitung ulang apa pun.` },
  ]);
  const insightPrompts = insights.filter((item) => item.status === "pending").slice(0, 2).map((item) => `Periksa ulang catatan saya untuk ${item.symbol}.`);
  const quickPrompts = [...insightPrompts, ...prompts.filter((prompt) => !insightPrompts.some((item) => item === prompt))];

  const submit = async (question: string) => {
    if (!question.trim() || loading) return;
    setMessages((current) => [...current, { id: `u-${current.length}`, role: "user", text: question.trim() }]);
    setInput("");
    setLoading(true);
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.trim(), profile, userInsights: insights }) });
      const body = await response.json();
      const answer = body.answer as ChatAnswer;
      setMessages((current) => [...current, { id: `a-${current.length}`, role: "assistant", text: answer.text, answer }]);
    } catch {
      setMessages((current) => [...current, { id: `e-${current.length}`, role: "assistant", text: "Route agent tidak merespons. Muat ulang lalu coba lagi." }]);
    } finally { setLoading(false); }
  };

  const onSubmit = (event: FormEvent) => { event.preventDefault(); void submit(input); };

  return (
    <div className={`flex h-full min-h-0 flex-col bg-surface ${workspace ? "rounded-[12px] border border-border" : ""}`}>
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <CatalystAvatar />
        <div className="min-w-0 flex-1">
          <p className="editorial text-[16px]">Catalyst Copilot</p>
          <p className="meta mt-1 truncate text-muted-foreground">{profile.name} · {insights.filter((item) => item.status === "pending").length} catatan terbuka</p>
        </div>
        {dismissible ? <Button variant="ghost" size="icon" onClick={() => setCopilotOpen(false)} aria-label="Tutup copilot"><IconClose className="size-4" /></Button> : null}
      </div>

      <p className="flex items-start gap-2 border-b border-border bg-surface-raised px-5 py-2.5 text-[11px] leading-[1.5] text-muted-foreground">
        <IconGate className="mt-0.5 size-3.5 shrink-0 text-positive" />
        Fakta, konflik, dan data kosong. Tidak menilai tindakan transaksi.
      </p>

      <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={message.role === "user" ? "pl-6" : ""}>
            <div className="mb-2 flex items-center gap-1.5">
              {message.role === "user" ? <IconUser className="size-3 text-muted-foreground" /> : <IconCopilot className="size-3 text-muted-foreground" />}
              <span className="meta text-muted-foreground">{message.role === "user" ? "Anda" : "Agent"}</span>
            </div>
            <div className={message.role === "user"
              ? "rounded-[8px] border-l-2 border-foreground bg-muted px-3.5 py-3 text-[13.5px] leading-[1.65]"
              : "text-[13.5px] leading-[1.65]"}>
              <p>{message.text}</p>
              {message.answer ? (
                <details className="group mt-3 border-t border-border pt-2.5">
                  <summary className="flex min-h-8 cursor-pointer list-none items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground">
                    <span className="meta">Periksa jawaban</span>
                    <IconCaretDown className="size-3 transition-transform group-open:rotate-180" />
                  </summary>
                  <p className="mt-2 text-[12px] leading-[1.6] text-muted-foreground">{message.answer.preferenceNote}</p>
                  {message.answer.hypotheses.some((item) => item.id.startsWith("insight-")) ? <p className="mt-2 rounded-[6px] bg-attention-soft p-2.5 text-[12px] leading-[1.6] text-attention">Catatan user hanya dipakai sebagai hipotesis terbuka sampai sumber memverifikasinya.</p> : null}
                  {message.answer.citations.length ? <div className="mt-3"><CitationDialog citations={message.answer.citations} label="Buka bukti jawaban" /></div> : null}
                </details>
              ) : null}
            </div>
          </div>
        ))}
        {loading ? (
          <p className="meta flex gap-1.5 text-muted-foreground" aria-label="Agent sedang membaca kartu">
            <span className="animate-pulse">Plan</span><span aria-hidden="true">→</span>
            <span className="animate-pulse [animation-delay:120ms]">Query</span><span aria-hidden="true">→</span>
            <span className="animate-pulse [animation-delay:240ms]">Verify</span>
          </p>
        ) : null}
      </div>

      <div className="border-t border-border p-4">
        <div className="mb-2.5 flex gap-2 overflow-x-auto pb-1">
          {(workspace ? quickPrompts : quickPrompts.slice(0, 3)).map((prompt) => (
            <button key={prompt} onClick={() => void submit(prompt)} className="min-h-9 shrink-0 cursor-pointer rounded-full border border-border px-3.5 text-[12px] text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">{prompt}</button>
          ))}
        </div>
        <form onSubmit={onSubmit} className="flex items-end gap-2 rounded-[8px] border border-border bg-background p-2 transition-colors focus-within:border-foreground/35">
          <label htmlFor="copilot-input" className="sr-only">Tanya Catalyst</label>
          <textarea id="copilot-input" rows={2} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(input); } }} placeholder="Tanya bukti atau dampak..." className="min-h-11 min-w-0 flex-1 resize-none bg-transparent px-2 py-2 text-[13.5px] outline-none placeholder:text-muted-foreground" />
          <Button type="submit" size="icon" disabled={!input.trim() || loading} aria-label="Kirim pertanyaan"><IconSend className="size-4" /></Button>
        </form>
        <p className="mt-2.5 flex items-center gap-1.5 text-[11px] text-muted-foreground"><IconExternal className="size-3" />Jawaban menyertakan provider, field, dan asOf bila tersedia.</p>
      </div>
    </div>
  );
}

function CatalystAvatar() {
  return (
    <span aria-hidden="true" className="grid size-9 shrink-0 place-items-center rounded-[8px] bg-foreground text-background">
      <IconCopilot className="size-4.5" />
    </span>
  );
}
