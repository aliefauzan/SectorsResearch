"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Extends the observer root upwards so a block still counts as intersecting
 * once it has passed above the viewport. Without it a jump — End, an anchor,
 * a restored scroll position — can carry a block from below the fold to above
 * it between two observer samples, and a block never sampled as intersecting
 * would stay hidden for good.
 */
const SKIPPED_MARGIN = 100_000;

/**
 * Scroll entry for a top-level block. Opacity and transform only, resolved
 * once.
 *
 * The invariant is that a block stays hidden only while something live can
 * still reveal it:
 *  - Content already on screen at load is never armed. It renders settled,
 *    which is also the only moment where a fade would be pure noise.
 *  - Arming happens only while the document is visible, since a hidden tab
 *    suspends observer delivery. The tab coming back arms whatever is still
 *    below the fold.
 *  - Teardown un-arms anything still waiting, so a re-run of this effect
 *    (Strict Mode does exactly that) cannot strand a block at opacity 0.
 */
export function Reveal({ children, className, index = 0 }: { children: ReactNode; className?: string; index?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element || typeof IntersectionObserver === "undefined") return;

    let observer: IntersectionObserver | undefined;

    const arm = () => {
      if (observer || document.visibilityState !== "visible") return;
      if (element.dataset.reveal !== "idle") return;
      if (element.getBoundingClientRect().top < window.innerHeight) return;

      element.dataset.reveal = "armed";
      observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          (entry.target as HTMLElement).dataset.reveal = "shown";
          observer?.unobserve(entry.target);
        });
      }, { rootMargin: `${SKIPPED_MARGIN}px 0px -4% 0px`, threshold: 0 });
      observer.observe(element);
    };

    arm();
    document.addEventListener("visibilitychange", arm);

    return () => {
      document.removeEventListener("visibilitychange", arm);
      observer?.disconnect();
      observer = undefined;
      if (element.dataset.reveal === "armed") element.dataset.reveal = "idle";
    };
  }, []);

  return (
    <div ref={ref} data-reveal="idle" style={{ "--reveal-index": index } as React.CSSProperties} className={cn("min-w-0", className)}>
      {children}
    </div>
  );
}
