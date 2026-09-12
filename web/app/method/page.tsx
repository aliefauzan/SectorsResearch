"use client";

import { useDataset } from "@/lib/dataset";
import { PageHeader } from "@/components/page-header";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Reveal } from "@/components/ui/reveal";
import { StatusBadge } from "@/components/ui/status-badge";
import { IconCode, IconDraftData, IconGate, IconScales, IconSource, IconVerified } from "@/components/ui/icons";

const pillars = [
  { name: "Konsentrasi", input: "/v2/broker-summary/, /v2/brokers/, /v2/foreign-flow/, /v2/free-float/", formula: "pangsa_puncak, hhi, pembeli_efektif, pangsa_asing, pangsa_kohort, float_terserap", output: "tenang · waspada · bahaya · tak terukur" },
  { name: "Volume", input: "/v2/daily/ dan baseline 45 hari bursa dari simbol itu sendiri", formula: "volume_puncak dan volume_z — median dan MAD, bukan rata-rata", output: "tenang · waspada · bahaya · tak terukur" },
  { name: "Momentum", input: "/v2/daily/ dan /v2/index-daily/ihsg/", formula: "return_kumulatif, return_residual setelah IHSG dikeluarkan, beta_efektif, residual_z", output: "tenang · waspada · bahaya · tak terukur" },
  { name: "Katalis", input: "/v2/news/, /v2/filings/, /v2/company/corporate-actions/", formula: "artikel_menjelaskan vs artikel_melaporkan, filing_material, aksi_korporasi — label, bukan hitungan sentimen", output: "tenang · waspada · bahaya · tak terukur" },
];

const stages = [
  "Reader memuat payload dari lapisan rekaman; tidak ada panggilan pasar baru.",
  "assess() menolak lebih dulu bila prasyaratnya tidak ada — dan menyebutkan alasannya.",
  "Empat pilar menghasilkan Figure: nilai, satuan, catatan, endpoint, dan field.",
  "verdict() memilih satu dari enam nama secara mekanis, lalu menambahkan penanda.",
  "jsonapi.py memproyeksikan Figure itu apa adanya; delapan gate melarangnya berhitung.",
  "Halaman ini memuat kartu di server dan menyerahkannya sekali ke peramban.",
  "Citation gate menolak metrik tanpa provider, endpoint, field, dan asOf.",
  "Language gate menahan kalimat yang menilai tindakan transaksi.",
  "Profil mengatur urutan pilar dan kedalaman; angka dan ambang tidak ikut berubah.",
  "Renderer membentuk kartu, jalur bukti, atau jawaban Copilot.",
];

const limits = [
  { icon: IconCode, title: "Tanpa panggilan baru", text: "Permukaan ini hanya membaca payload Sectors yang sudah direkam. Ia tidak memanggil API berbayar saat halaman dibuka." },
  { icon: IconDraftData, title: "Tanpa intraday", text: "Chart memakai daily close dan volume. Order book dan antrean tidak tersedia." },
  { icon: IconScales, title: "Tanpa motif", text: "Kode broker ditampilkan sebagai fakta transaksi, bukan atribusi niat." },
  { icon: IconGate, title: "Tanpa aksi", text: "Output berhenti pada bukti, konflik, dan informasi yang belum ada." },
];

export default function MethodPage() {
  const { analyses, source } = useDataset();
  // The thresholds are read off a served card rather than restated here, so the table on this
  // page cannot drift from the table the verdict actually used.
  const thresholds = Object.values(analyses)[0]?.thresholds ?? [];
  const learned = thresholds.filter((entry) => entry.origin === "learned").length;

  return (
    <div className="mx-auto max-w-[1180px]">
      <PageHeader
        eyebrow="Method and limits"
        title="Cara kartu ini disusun"
        description={`Empat pilar, ${thresholds.length} ambang, satu verdict mekanis. Angka dihitung oleh KATALIS di sisi server dari payload Sectors yang sudah direkam — sumber ${source || "—"} — dan halaman ini tidak menghitung ulang satu pun di antaranya.`}
      />

      <Reveal>
        <Panel>
          <PanelHeader eyebrow="Four-pillar model" title="Tidak ada skor daya tarik gabungan" />
          <div className="grid gap-px bg-border md:grid-cols-2">
            {pillars.map((pillar, index) => (
              <article key={pillar.name} className="bg-surface px-6 py-6">
                <div className="flex items-baseline gap-3.5">
                  <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                  <h2 className="editorial text-[21px]">{pillar.name}</h2>
                </div>
                <dl className="mt-5 space-y-4 text-[13px]">
                  <div>
                    <dt className="meta text-muted-foreground">Endpoint yang dibaca</dt>
                    <dd className="mt-1.5 leading-[1.65]">{pillar.input}</dd>
                  </div>
                  <div>
                    <dt className="meta text-muted-foreground">Figure yang dihasilkan</dt>
                    <dd className="mt-1.5 leading-[1.65]">{pillar.formula}</dd>
                  </div>
                  <div>
                    <dt className="meta text-muted-foreground">Output</dt>
                    <dd className="mt-1.5 leading-[1.65] text-muted-foreground">{pillar.output}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </Panel>
      </Reveal>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Reveal>
          <Panel className="h-full">
            <PanelHeader eyebrow="Orchestration" title="Sepuluh tahap agent" />
            <ol className="divide-y divide-border">
              {stages.map((item, index) => (
                <li key={item} className="flex gap-4 px-5 py-3.5 text-[13px] leading-[1.65]">
                  <span className="font-mono text-[11px] tabular-nums text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                  <span>{item}</span>
                </li>
              ))}
            </ol>
          </Panel>
        </Reveal>

        <div className="space-y-6">
          <Reveal index={1}>
            <Panel>
              <PanelHeader eyebrow="Data contract" title="Citation gate" />
              <div className="px-5 py-5">
                <p className="flex gap-3 text-[13px] leading-[1.7]">
                  <IconSource className="mt-1 size-4 shrink-0 text-muted-foreground" />
                  Setiap angka output membawa provider, endpoint, field, dan asOf. Metrik tanpa keempatnya membuat kartunya gagal dibangun, di sisi Python maupun di sini.
                </p>
                <pre tabIndex={0} className="mt-4 overflow-x-auto rounded-[6px] bg-muted px-3.5 py-3 font-mono text-[11.5px] leading-[1.7] text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><code>{`{ provider, endpoint, field, asOf, url, access }`}</code></pre>
              </div>
            </Panel>
          </Reveal>

          <Reveal index={2}>
            <Panel>
              <PanelHeader eyebrow="Human collaboration" title="Terlihat, dapat dibalik, dapat dihapus" />
              <ul className="divide-y divide-border">
                {["Koreksi user disimpan sebagai hipotesis terbuka", "Status review dapat dikembalikan ke antrean", "Catatan tidak mengubah fakta atau formula", "Seluruh memori dapat dihapus dari Agent Studio"].map((item) => (
                  <li key={item} className="flex items-center gap-3 px-5 py-3 text-[13px]">
                    <IconVerified className="size-3.5 shrink-0 text-positive" />{item}
                  </li>
                ))}
              </ul>
            </Panel>
          </Reveal>
        </div>
      </div>

      <Reveal className="mt-6">
        <Panel>
          <PanelHeader eyebrow="Ambang" title={`${thresholds.length} angka yang memutuskan setiap status`} />
          <div className="overflow-x-auto px-5 py-5">
            <table className="w-full min-w-[420px] text-left text-[12.5px]">
              <caption className="sr-only">Ambang yang dipakai kartu pada sumber ini</caption>
              <thead>
                <tr className="border-b border-border">
                  <th className="meta py-2 pr-4 font-normal text-muted-foreground">Ambang</th>
                  <th className="meta py-2 pr-4 text-right font-normal text-muted-foreground">Nilai</th>
                  <th className="meta py-2 font-normal text-muted-foreground">Asal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono tabular-nums">
                {thresholds.map((entry) => (
                  <tr key={entry.name}>
                    <td className="py-2 pr-4">{entry.name}</td>
                    <td className="py-2 pr-4 text-right">{entry.value}</td>
                    <td className="py-2 font-[family-name:var(--font-sans)]"><StatusBadge status={entry.origin} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 text-[12px] leading-[1.65] text-muted-foreground">{learned} dipelajari dari peristiwa berlabel, {thresholds.length - learned} ditulis tangan. Tabel ini dibaca dari kartu yang dilayani, bukan ditulis ulang di halaman ini, jadi ia tidak bisa menyimpang dari ambang yang benar-benar dipakai.</p>
          </div>
        </Panel>
      </Reveal>

      <Reveal className="mt-6">
        <Panel>
          <PanelHeader eyebrow="Known limits" title="Faktor yang belum diperiksa" />
          <div className="grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">
            {limits.map((item) => (
              <article key={item.title} className="bg-surface px-5 py-6">
                <item.icon className="size-4.5 text-muted-foreground" />
                <h3 className="mt-4 text-[13.5px] font-medium">{item.title}</h3>
                <p className="mt-2 text-[12.5px] leading-[1.65] text-muted-foreground">{item.text}</p>
              </article>
            ))}
          </div>
          <p className="border-t border-border px-6 py-6 text-[13px] leading-[1.75]">
            <strong className="font-medium">Disclaimer.</strong> Ini alat riset. Payload yang dibacanya adalah rekaman bertanggal, bukan kondisi pasar saat ini — setiap kartu mencantumkan tanggalnya sendiri. Output berhenti pada bukti: tidak ada target harga, tidak ada penilaian tindakan transaksi, dan tidak ada skor gabungan.
          </p>
        </Panel>
      </Reveal>
    </div>
  );
}
