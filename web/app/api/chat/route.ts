import { NextResponse } from "next/server";
import { createEngine } from "@/lib/agent/engine";
import { loadDataset } from "@/lib/katalis/load";
import { chatRequestSchema } from "@/lib/schemas";
import type { SymbolCode, UserInsight, UserProfile } from "@/lib/types";

export async function POST(request: Request) {
  try {
    const parsed = chatRequestSchema.safeParse(await request.json());
    if (!parsed.success) return NextResponse.json({ error: "Pertanyaan atau profil tidak valid", details: parsed.error.flatten() }, { status: 400 });
    const dataset = await loadDataset();
    if (dataset.error) return NextResponse.json({ error: dataset.error }, { status: 502 });
    const answer = createEngine(dataset).answerFollowUp({
      question: parsed.data.question,
      profile: parsed.data.profile as UserProfile,
      contextSymbol: parsed.data.contextSymbol as SymbolCode | undefined,
      userInsights: parsed.data.userInsights as UserInsight[] | undefined,
    });
    return NextResponse.json({ answer, source: dataset.source, api: dataset.baseUrl });
  } catch {
    return NextResponse.json({ error: "Body request tidak dapat dibaca" }, { status: 400 });
  }
}
