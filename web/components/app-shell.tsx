"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useState } from "react";
import { CatalystLogo } from "@/components/logo";
import { CommandPalette } from "@/components/command-palette";
import { Copilot } from "@/components/copilot";
import { Button } from "@/components/ui/button";
import {
  IconAgent,
  IconClose,
  IconCompanies,
  IconCopilot,
  IconMethod,
  IconImpact,
  IconMenu,
  IconMoon,
  IconSun,
  IconToday,
} from "@/components/ui/icons";
import { useDataset } from "@/lib/dataset";
import { useCatalystStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Today", icon: IconToday },
  { href: "/companies", label: "Companies", icon: IconCompanies },
  { href: "/impact", label: "Impact map", icon: IconImpact },
  { href: "/copilot", label: "Copilot", icon: IconCopilot },
  { href: "/agent", label: "Agent", icon: IconAgent },
  { href: "/method", label: "Method", icon: IconMethod },
];

const OnboardingWizard = dynamic(() => import("@/components/onboarding-wizard").then((mod) => mod.OnboardingWizard), { ssr: false });

export function AppShell({ children }: { children: React.ReactNode }) {
  const { source, asOf } = useDataset();
  const synthetic = source === "synth";
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const [mobileNav, setMobileNav] = useState(false);
  const copilotOpen = useCatalystStore((state) => state.copilotOpen);
  const copilotPage = pathname.startsWith("/copilot");
  const widePage = copilotPage || pathname.startsWith("/impact");
  const mobileNavItems = navItems.filter((item) => item.href !== "/method");
  const toggleTheme = () => setTheme(resolvedTheme === "dark" ? "light" : "dark");

  const nav = (onNavigate?: () => void) => navItems.map((item) => {
    const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onNavigate}
        aria-current={active ? "page" : undefined}
        className={cn(
          "relative flex min-h-10 cursor-pointer items-center gap-3 rounded-[6px] px-3 text-[13px] transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          active ? "bg-muted font-medium text-foreground" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
        )}
      >
        {active ? <span aria-hidden="true" className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-full bg-foreground" /> : null}
        <item.icon className="size-4 shrink-0" />
        <span>{item.label}</span>
      </Link>
    );
  });

  return (
    <div className="relative min-h-dvh bg-background">
      <div className="ambient" aria-hidden="true" />
      <a href="#main-content" className="skip-link">Lewati navigasi</a>

      {/*
        The banner names the source and the date, because those are the two things a reader
        can be wrong about. On `recorded` these are real Sectors payloads captured on a fixed
        date — not live, and not simulated. On `synth` they are generated, and the banner has
        to say so on every screen: shipping generated numbers as the product's data is the one
        thing the rules forbid outright.
      */}
      <div className="demo-banner relative z-50 flex h-9 items-center justify-center gap-2.5 border-b border-border bg-attention-soft px-3 text-center">
        <span aria-hidden="true" className="size-1.5 shrink-0 rounded-full bg-attention" />
        <p className="meta truncate text-attention">
          <strong className="font-medium">{synthetic ? "Data sintetis" : "Rekaman"}</strong>
          <span aria-hidden="true" className="mx-2 opacity-50">/</span>
          <span className="sm:hidden">{synthetic ? "bukan data pasar" : `Sectors · ${asOf ?? "—"}`}</span>
          <span className="hidden sm:inline">
            {synthetic
              ? "dibangkitkan untuk uji beban, bukan data pasar"
              : `payload Sectors terekam ${asOf ?? "—"}, bukan kondisi pasar terkini`}
          </span>
        </p>
      </div>

      <div className={cn("relative z-10 grid min-h-[calc(100dvh-36px)]", widePage ? "xl:grid-cols-[236px_minmax(0,1fr)]" : "xl:grid-cols-[236px_minmax(0,1fr)_372px]")}>
        <aside className="sticky top-0 hidden h-[calc(100dvh-36px)] flex-col border-r border-border bg-surface px-3 py-4 xl:flex">
          <Link href="/" className="mb-6 flex min-h-12 items-center gap-3 rounded-[6px] px-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <CatalystLogo className="size-8 shrink-0" />
            <span className="min-w-0">
              <span className="editorial block text-[17px] text-foreground">Catalyst</span>
              <span className="meta block text-muted-foreground">Evidence agent</span>
            </span>
          </Link>

          <CommandPalette />

          <nav aria-label="Navigasi utama" className="mt-5 space-y-0.5">{nav()}</nav>

          <div className="mt-auto border-t border-border pt-4">
            <p className="editorial mb-3 px-2 text-[15px] italic text-muted-foreground">Empat bukti untuk setiap gerak.</p>
            <Button variant="ghost" size="sm" className="w-full justify-start" onClick={toggleTheme}>
              <IconSun className="size-4 dark:hidden" />
              <IconMoon className="hidden size-4 dark:block" />
              <span>Ganti tema</span>
            </Button>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="sticky top-0 z-40 flex min-h-14 items-center gap-3 border-b border-border bg-background/92 px-3 backdrop-blur-md sm:px-5 xl:hidden">
            <Button variant="ghost" size="icon" onClick={() => setMobileNav(true)} aria-label="Buka navigasi"><IconMenu className="size-5" /></Button>
            <Link href="/" className="flex min-w-0 items-center gap-2.5">
              <CatalystLogo className="size-7" />
              <span className="editorial text-[16px] text-foreground">Catalyst</span>
            </Link>
            <div className="ml-auto flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Ganti tema">
                <IconSun className="size-4 dark:hidden" />
                <IconMoon className="hidden size-4 dark:block" />
              </Button>
              <Link href="/copilot" className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-[6px] border border-border bg-surface px-3 text-xs font-medium transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <IconCopilot className="size-4" />
                <span className="hidden sm:inline">Tanya agent</span>
                <span className="sr-only sm:hidden">Buka copilot</span>
              </Link>
            </div>
          </header>

          <main id="main-content" tabIndex={-1} className="min-w-0 px-4 pb-24 pt-6 focus:outline-none sm:px-7 sm:pt-8 lg:px-9 lg:pt-10 xl:pb-10">{children}</main>

          <nav aria-label="Navigasi mobile" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-border bg-surface/97 px-1 backdrop-blur-md pb-[env(safe-area-inset-bottom)] xl:hidden">
            {mobileNavItems.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined} className={cn("flex min-h-14 cursor-pointer flex-col items-center justify-center gap-1 rounded-[6px] text-[10px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", active ? "font-medium text-foreground" : "text-muted-foreground")}>
                  <item.icon className="size-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {!widePage ? <aside className="sticky top-0 hidden h-[calc(100dvh-36px)] border-l border-border xl:block"><Copilot /></aside> : null}
      </div>

      {mobileNav ? (
        <div className="fixed inset-0 z-100 xl:hidden">
          <button className="absolute inset-0 cursor-default bg-foreground/45 backdrop-blur-[2px]" onClick={() => setMobileNav(false)} aria-label="Tutup navigasi" />
          <aside className="absolute inset-y-0 left-0 w-[min(86vw,300px)] border-r border-border bg-surface p-4">
            <div className="mb-6 flex items-center gap-3">
              <CatalystLogo className="size-8" />
              <span className="editorial text-[17px]">Catalyst</span>
              <Button variant="ghost" size="icon" className="ml-auto" onClick={() => setMobileNav(false)} aria-label="Tutup navigasi"><IconClose className="size-4" /></Button>
            </div>
            <nav className="space-y-0.5">{nav(() => setMobileNav(false))}</nav>
            <div className="mt-7"><CommandPalette /></div>
          </aside>
        </div>
      ) : null}

      {copilotOpen ? <div className="fixed inset-0 z-100 bg-surface xl:hidden"><Copilot dismissible /></div> : null}
      <OnboardingWizard />
    </div>
  );
}
