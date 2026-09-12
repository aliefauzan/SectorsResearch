import { NextResponse } from "next/server";
import { impactRequestSchema } from "@/lib/schemas";

/**
 * Kept, and kept honest.
 *
 * KATALIS counts the articles, filings and corporate actions inside an event window and
 * reports those counts through the katalis pillar. It does not publish event objects, impact
 * links, or relevance scores, so there is nothing for this route to map. It validates the
 * request the same way the others do and then says exactly that, rather than returning a
 * shape the product cannot stand behind.
 */
export async function POST(request: Request) {
  try {
    const parsed = impactRequestSchema.safeParse(await request.json());
    if (!parsed.success) return NextResponse.json({ error: "Input peta dampak tidak valid", details: parsed.error.flatten() }, { status: 400 });
    return NextResponse.json({
      error: "Produk ini tidak memproduksi jalur dampak peristiwa",
      detail: "Pilar katalis melaporkan jumlah kabar, filing, dan aksi korporasi dalam jendela peristiwa. Ia tidak menghasilkan tautan sebab-akibat antar-emiten, dan permukaan ini tidak mengarangnya.",
    }, { status: 501 });
  } catch {
    return NextResponse.json({ error: "Body request tidak dapat dibaca" }, { status: 400 });
  }
}
