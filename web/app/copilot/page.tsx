import { Copilot } from "@/components/copilot";
import { PageHeader } from "@/components/page-header";
import { IconGate, IconNote, IconSearch } from "@/components/ui/icons";

const limits = [
  { icon: IconSearch, text: "Membaca kartu, bukan menghitung ulang" },
  { icon: IconGate, text: "Fail-closed tanpa bukti" },
  { icon: IconNote, text: "Catatan user jadi hipotesis" },
];

export default function CopilotPage() {
  return (
    <div className="mx-auto max-w-[1180px]">
      <PageHeader eyebrow="AI research desk" title="Cari jawaban dari bukti yang sudah diperiksa" description="Tanyakan satu ticker, bandingkan dua emiten, atau tanyakan apa yang belum diperiksa. Jawaban dibatasi kartu yang sudah dinilai KATALIS dan selalu membawa ledger sumbernya." />

      <ul className="mb-5 grid gap-px border-y border-border bg-border sm:grid-cols-3" aria-label="Batas copilot">
        {limits.map((item) => (
          <li key={item.text} className="flex items-center gap-2.5 bg-background px-1 py-3 text-[12px] text-muted-foreground sm:px-4">
            <item.icon className="size-3.5 shrink-0" />{item.text}
          </li>
        ))}
      </ul>

      <div className="h-[calc(100dvh-310px)] min-h-[460px]"><Copilot workspace /></div>
    </div>
  );
}
