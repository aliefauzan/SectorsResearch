import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("id-ID").format(value);
}

export function formatCurrency(value: number) {
  // id-ID separates the symbol with a non-breaking space, which reads as a
  // double gap once the number is set in a tabular mono face.
  return new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 })
    .format(value)
    .replace(/\u00a0/g, " ");
}

export function formatAsOf(value: string) {
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta",
  }).format(new Date(value));
}

/** A value the payload does not carry is an em dash, never a zero and never a blank. */
export function orDash(value: string | null | undefined): string {
  return value ?? "—";
}

/** A signed percentage from a fraction, or an em dash when no payload carries the change. */
export function formatPercentChange(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("id-ID", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: "exceptZero" }).format(value);
}
