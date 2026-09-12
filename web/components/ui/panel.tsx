import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Panel({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <section className={cn("relative rounded-[12px] border border-border bg-surface", className)} {...props} />;
}

export function PanelHeader({ title, eyebrow, action }: { title: string; eyebrow?: string; action?: ReactNode }) {
  return (
    <div className="flex min-w-0 items-start justify-between gap-4 border-b border-border px-5 py-4">
      <div className="min-w-0">
        {eyebrow ? <p className="meta mb-1.5 text-muted-foreground">{eyebrow}</p> : null}
        <h2 className="editorial text-[17px] text-foreground">{title}</h2>
      </div>
      {action}
    </div>
  );
}
