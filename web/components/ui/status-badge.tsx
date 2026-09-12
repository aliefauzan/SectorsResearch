import { IconAttention, IconConflict, IconNeutral, IconUnknown, IconVerified } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

/**
 * The vocabulary this badge colours is KATALIS's, and it is Indonesian.
 *
 * Four pillar statuses (`tenang`, `waspada`, `bahaya`, `tak terukur`), six verdict names, and
 * the two threshold origins. A status the product can emit but this function does not know
 * would fall through to the neutral tone rather than being coloured wrongly, which is the
 * right failure: a mis-coloured danger reads as safe.
 */
function toneFor(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes("bahaya") || normalized.includes("tanpa penjelasan") || normalized.includes("tiga pilar")) return "negative";
  if (normalized.includes("waspada") || normalized.includes("dominan") || normalized.includes("menyala") || normalized.includes("terkonsentrasi")) return "attention";
  if (normalized.includes("tenang") || normalized.includes("tidak ada yang menonjol")) return "positive";
  if (normalized.includes("tak terukur") || normalized.includes("tidak dinilai") || normalized.includes("belum dinilai")) return "muted";
  if (normalized === "shipped") return "info";
  if (normalized === "learned") return "attention";
  return "info";
}

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const tone = toneFor(status);
  const Icon = tone === "positive" ? IconVerified : tone === "negative" ? IconConflict : tone === "attention" ? IconAttention : tone === "muted" ? IconUnknown : IconNeutral;
  return (
    <span className={cn(
      "inline-flex max-w-full items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium uppercase leading-none tracking-[0.07em]",
      tone === "positive" && "bg-positive-soft text-positive",
      tone === "negative" && "bg-danger-soft text-danger",
      tone === "attention" && "bg-attention-soft text-attention",
      tone === "muted" && "bg-muted text-muted-foreground",
      tone === "info" && "bg-accent-soft text-accent",
      className,
    )}>
      <Icon className="size-3 shrink-0" />
      <span className="truncate">{status}</span>
    </span>
  );
}
