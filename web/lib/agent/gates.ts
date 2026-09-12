import type { Citation, PillarResult } from "@/lib/types";

export function isCompleteCitation(citation: Citation): boolean {
  return Boolean(citation.provider && citation.endpoint && citation.field && citation.asOf);
}

export function enforceCitations(pillars: PillarResult[]): void {
  for (const pillar of pillars) {
    for (const metric of pillar.metrics) {
      if (metric.citations.length === 0 || metric.citations.some((citation) => !isCompleteCitation(citation))) {
        throw new Error(`Citation gate: ${pillar.key}/${metric.label} tidak memiliki sumber lengkap`);
      }
    }
  }
}

const ADVICE_PATTERN = /\b(beli|jual|entry|stop\s*loss|target\s*price|take\s*profit|cuan|buy|sell)\b/i;

export function safeLanguage(input: string): { refused: boolean; text: string } {
  if (ADVICE_PATTERN.test(input)) {
    return {
      refused: true,
      text: "Catalyst tidak menilai tindakan transaksi. Saya dapat merangkum bukti Konsentrasi, Volume, Momentum, dan Katalis beserta data yang masih kosong.",
    };
  }
  return { refused: false, text: input };
}

export function assertSafeOutput(text: string): void {
  if (ADVICE_PATTERN.test(text)) {
    throw new Error("Language gate: output memuat istilah advisory atau transaksi");
  }
}
