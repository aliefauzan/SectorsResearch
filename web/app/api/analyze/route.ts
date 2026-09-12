import { NextResponse } from "next/server";
import { createEngine } from "@/lib/agent/engine";
import { loadDataset } from "@/lib/katalis/load";
import { analyzeRequestSchema } from "@/lib/schemas";
import type { UserProfile } from "@/lib/types";

export async function POST(request: Request) {
  try {
    const parsed = analyzeRequestSchema.safeParse(await request.json());
    if (!parsed.success) return NextResponse.json({ error: "Input analisis tidak valid", details: parsed.error.flatten() }, { status: 400 });
    const dataset = await loadDataset();
    if (dataset.error) return NextResponse.json({ error: dataset.error }, { status: 502 });
    const analysis = createEngine(dataset).analyzeCompany(parsed.data.symbol, parsed.data.profile as UserProfile);
    if (!analysis) {
      const reason = dataset.rejected[parsed.data.symbol] ?? "Simbol ini tidak dilayani sumber yang sedang aktif";
      return NextResponse.json({ error: reason }, { status: 404 });
    }
    return NextResponse.json({ analysis, source: dataset.source, api: dataset.baseUrl });
  } catch {
    return NextResponse.json({ error: "Body request tidak dapat dibaca" }, { status: 400 });
  }
}
