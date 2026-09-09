import sys
sys.path.insert(0, "/Users/af/.claude/plugins/cache/orthogram/orthogram/0.2.0/skills/drawing-flowcharts")
import flow_drawio as F
from flow_drawio import Flow, FLOW, YES_C, NO_C, ALT, NOTE
from diagram_kit.geometry import L, R, T, B

F.COL_PITCH = 520

f = Flow("Riset saham IDX yang bisa didengar — alur input, proses, output",
         "sumber data · pipeline · permukaan ke pengguna")

f.pool("Sumber data (Sectors API)", cols=[0])
f.pool("Pipeline", cols=[1])
f.pool("Permukaan ke pengguna", cols=[2])

s      = f.start   ("Pengguna membuka satu emiten",              col=1, row=0)
inp    = f.io      ("Input: kode saham + pertanyaan opsional",   col=1, row=1)
plan   = f.process ("P0 · Planner pilih section, sadar kredit",  col=1, row=2)
fetch  = f.process ("P1 · Tarik data yang biasanya divisualkan", col=1, row=3)
avail  = f.decision("Datanya kembali?",                          col=1, row=4)
say    = f.process ("P2 · Susun kalimat tingkat 2-3: tren, ekstrem, perbandingan", col=1, row=5)
lang   = f.process ("P3 · Render angka jadi bahasa terucap",     col=1, row=6)
cite   = f.decision("Tiap angka punya (endpoint, field)?",       col=1, row=7)
audio  = f.decision("Audio dinyalakan?",                         col=1, row=8)
out    = f.io      ("Output teks: ringkasan lebih dulu, lalu bagian, tabel, sitasi", col=1, row=9)
done   = f.terminal("Pengguna menavigasi lewat heading dan tanya-jawab", col=1, row=10)

src    = f.store   ("report?sections=peers\nget-segments · daily\nshareholders-composition", col=0, row=3)
redo   = f.process ("Ambil ulang field yang tak bersumber",      col=0, row=7)
honest = f.terminal("Katakan 'belum diambil' · jangan mengarang", col=2, row=4)
son    = f.process ("P5 · Sonifikasi tren + earcon event",       col=2, row=8)

n1 = f.note("Tingkat 1 (mark, sumbu, encoding) tidak pernah diucapkan — Lundgard & Satyanarayan", col=0, row=5)
n2 = f.note("Volatilitas dan perbandingan multi-indikator diucapkan sebagai angka, tidak disonifikasi — Fu 2026", col=2, row=9)

f.then(s, inp)
f.then(inp, plan)
f.then(plan, fetch)
f.then(fetch, avail)
f.branch(avail, yes=say, no=honest,
         yes_label="Ya · lanjut menyusun", no_label="Tidak · fail-closed")
f.then(say, lang)
f.then(lang, cite)
f.branch(cite, yes=audio, no=redo,
         yes_label="Ya · tiap angka bersitasi", no_label="Tidak · tolak draf")
f.to(redo, fetch, "Ambil ulang", ALT,
     exit=T(0.5), entry=L(0.72), corridor=f.corridor(after_col=0))
f.branch(audio, yes=son, no=out,
         yes_label="Ya · tambah lapisan audio", no_label="Tidak · teks saja")
f.to(son, out, "Sonifikasi menempel pada teks yang sama", FLOW,
     exit=L(0.5), entry=R(0.5), corridor=f.corridor(after_col=1))
f.then(out, done)

f.to(src, fetch, "1 kredit per section", NOTE,
     exit=R(0.5), entry=L(0.28), corridor=f.corridor(after_col=0), dashed=True)

f.legend(FLOW,  "alur utama")
f.legend(YES_C, "kondisi terpenuhi")
f.legend(NO_C,  "kondisi gagal · berhenti atau ditolak")
f.legend(ALT,   "pengambilan ulang")
f.legend(NOTE,  "sumber data", dashed=True)

f.write("research/plan/tunanetra/diagrams/alur.drawio")
print("written")
