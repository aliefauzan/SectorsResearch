"use client";

import * as Tabs from "@radix-ui/react-tabs";
import type { HypothesisTrace } from "@/lib/types";
import { IconAttention, IconInspect, IconUnknown, IconVerified } from "@/components/ui/icons";

export function AgentTrace({ traces }: { traces: HypothesisTrace[] }) {
  return (
    <Tabs.Root defaultValue="0" className="rounded-[12px] border border-border bg-surface">
      <div className="border-b border-border px-5 py-4">
        <p className="meta text-muted-foreground">Simulasi agent</p>
        <h2 className="editorial mt-1.5 text-[17px]">Plan → Query → Verify → Summarize</h2>
      </div>
      <Tabs.List aria-label="Hipotesis agent" className="flex gap-1 overflow-x-auto border-b border-border px-3 py-2">
        {traces.map((trace, index) => (
          <Tabs.Trigger key={trace.id} value={String(index)} className="min-h-9 shrink-0 cursor-pointer rounded-[6px] px-3 font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground data-[state=active]:bg-foreground data-[state=active]:text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">H{index + 1}</Tabs.Trigger>
        ))}
      </Tabs.List>
      {traces.map((trace, index) => (
        <Tabs.Content key={trace.id} value={String(index)} className="px-5 py-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 shrink-0">
              {trace.outcome === "supported" ? <IconVerified className="size-4 text-positive" />
                : trace.outcome === "challenged" ? <IconAttention className="size-4 text-attention" />
                : <IconUnknown className="size-4 text-muted-foreground" />}
            </span>
            <div className="min-w-0">
              <h3 className="text-[14px] font-medium leading-[1.5]">{trace.hypothesis}</h3>
              <p className="mt-2 text-[13px] leading-[1.65] text-muted-foreground">{trace.verification}</p>
            </div>
          </div>
          <div className="mt-5 flex gap-3 border-t border-border pt-4">
            <IconInspect className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
            <div className="min-w-0">
              <p className="meta text-muted-foreground">Fixture query</p>
              <p className="mt-1.5 font-mono text-[11.5px] leading-[1.7]">{trace.query}</p>
            </div>
          </div>
        </Tabs.Content>
      ))}
    </Tabs.Root>
  );
}
