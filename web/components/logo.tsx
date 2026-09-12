import { cn } from "@/lib/utils";

/**
 * The mark reads as a catalysed reaction: an open arc that never closes,
 * with four rising ticks for the four pillars. Knockout glyph so it
 * inverts with the theme without a second asset.
 */
export function CatalystLogo({ className }: { className?: string }) {
  return (
    <svg className={cn("size-8", className)} viewBox="0 0 32 32" aria-hidden="true">
      <rect x="0.5" y="0.5" width="31" height="31" rx="7.5" fill="currentColor" />
      <path d="M20.8 10.6a7.2 7.2 0 1 0 0 10.8" fill="none" stroke="var(--surface)" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M20.4 20.4v-3.1M23.6 20.4v-5.8M26.8 20.4v-8.5" stroke="var(--surface)" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}
