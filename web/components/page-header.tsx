import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-col gap-6 border-b border-border pb-7 sm:flex-row sm:items-end sm:justify-between sm:gap-10">
      <div className="min-w-0 max-w-3xl">
        <p className="meta text-muted-foreground">{eyebrow}</p>
        <h1 className="editorial mt-3 text-[30px] sm:text-[38px]">{title}</h1>
        <p className="mt-3 max-w-2xl text-[13.5px] leading-[1.65] text-muted-foreground">{description}</p>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}
