import type { PillarResult } from "@/lib/types";
import { CitationDialog } from "@/components/citation-dialog";
import { StatusBadge } from "@/components/ui/status-badge";
import { IconConflict, IconSource } from "@/components/ui/icons";

export function EvidenceCard({ pillar, index }: { pillar: PillarResult; index: number }) {
  return (
    <article className="flex min-w-0 max-w-full flex-col rounded-[12px] border border-border bg-surface transition-shadow duration-200 hover:shadow-lift">
      <div className="flex items-start gap-4 px-5 pt-5">
        <span className="mt-0.5 font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
        <div className="min-w-0 flex-1">
          <p className="meta text-muted-foreground">Pilar bukti</p>
          <h3 className="editorial mt-1.5 text-[19px]">{pillar.label}</h3>
        </div>
        <StatusBadge status={pillar.status} />
      </div>

      <div className="px-5 pb-6 pt-3.5">
        <p className="text-[13.5px] leading-[1.65] text-muted-foreground">{pillar.summary}</p>
        {pillar.conflict ? (
          <p className="mt-4 flex gap-2.5 rounded-[8px] bg-danger-soft p-3 text-[12px] leading-[1.6] text-danger">
            <IconConflict className="mt-0.5 size-3.5 shrink-0" />
            {pillar.conflict}
          </p>
        ) : null}
      </div>

      <dl className="mt-auto grid grid-cols-2 border-t border-border">
        {pillar.metrics.slice(0, 2).map((metric, position) => (
          <div key={metric.label} className={`min-w-0 px-5 py-4 ${position === 0 ? "border-r border-border" : ""}`}>
            <dt className="truncate text-[11px] text-muted-foreground" title={metric.label}>{metric.label}</dt>
            <dd className="mt-1.5 break-words font-mono text-[17px] tabular-nums">{metric.value}</dd>
            <dd className="meta mt-1.5 inline-flex items-center gap-1 text-muted-foreground"><IconSource className="size-2.5" />{metric.citations.length} source</dd>
          </div>
        ))}
      </dl>

      <details className="group border-t border-border">
        <summary className="flex min-h-12 cursor-pointer list-none items-center gap-3 px-5 text-[12px] font-medium transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
          Lihat perhitungan dan semua input
          <span aria-hidden="true" className="ml-auto font-mono text-[15px] leading-none text-muted-foreground">
            <span className="group-open:hidden">+</span>
            <span className="hidden group-open:inline">−</span>
          </span>
        </summary>
        <div className="border-t border-border px-5 py-5">
          {pillar.calculation ? (
            <div>
              <p className="meta text-muted-foreground">{pillar.calculation.name}</p>
              <code className="mt-2.5 block overflow-x-auto rounded-[6px] bg-muted px-3 py-2.5 font-mono text-[11.5px] leading-[1.7]">{pillar.calculation.formula}</code>
              <dl className="mt-4 space-y-3 text-[12px]">
                <div>
                  <dt className="text-muted-foreground">Substitusi</dt>
                  <dd className="mt-1 break-words font-mono leading-[1.6]">{pillar.calculation.substitution}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Hasil deterministik</dt>
                  <dd className="mt-1 font-mono font-medium">{pillar.calculation.result}</dd>
                </div>
              </dl>
              <ul className="mt-4 space-y-2 text-[12px] leading-[1.6] text-muted-foreground">
                {pillar.calculation.notes.map((note) => (
                  <li key={note} className="flex gap-2.5"><span aria-hidden="true" className="mt-[9px] h-px w-2 shrink-0 bg-border" />{note}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {pillar.metrics.length > 2 ? (
            <dl className="mt-5 grid grid-cols-2 gap-x-5 gap-y-3 border-t border-border pt-4 sm:grid-cols-3">
              {pillar.metrics.slice(2).map((metric) => (
                <div key={metric.label}>
                  <dt className="text-[10px] text-muted-foreground">{metric.label}</dt>
                  <dd className="mt-1 break-words font-mono text-[12px] tabular-nums">{metric.value}</dd>
                </div>
              ))}
            </dl>
          ) : null}

          <div className="mt-5"><CitationDialog citations={pillar.citations} label="Periksa field sumber" /></div>
        </div>
      </details>
    </article>
  );
}
