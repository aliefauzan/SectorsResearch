import sys
sys.path.insert(0, "/Users/af/.claude/plugins/cache/orthogram/orthogram/0.2.0/skills/drawing-flowcharts")
import flow_drawio as F
from flow_drawio import Flow, FLOW, YES_C, NO_C, ALT, NOTE
from diagram_kit.geometry import L, R, T, B

F.COL_PITCH = 540

f = Flow("Firewall pra-transaksi untuk tip saham media sosial — alur input, proses, output",
         "sumber data · pipeline pemeriksa · keluaran dan evaluasi")

f.pool("Sumber data (Sectors API)", cols=[0])
f.pool("Pipeline pemeriksa",        cols=[1])
f.pool("Keluaran dan evaluasi",     cols=[2])

s     = f.start   ("Tip saham masuk dari grup chat",             col=1, row=0)
inp   = f.io      ("Input: 1 kode saham (+ teks tip, konteks saja)", col=1, row=1)
p1    = f.process ("P1 · Hitung baseline 5 hari: mean dan SD",   col=1, row=2)
d1    = f.decision("Harga DAN volume lewat 2 SD?",               col=1, row=3)
p2    = f.process ("P2 · Ukur konsentrasi 5 broker teratas, dibobot kohort", col=1, row=4)
p3    = f.process ("P3 · Baca rotasi kepemilikan dan arus asing", col=1, row=5)
d2    = f.decision("P4 · Ada berita fundamental di jendela sama?", col=1, row=6)
p4    = f.process ("P6 · Susun vonis 4 sumbu dengan sitasi",      col=1, row=7)
d3    = f.decision("Tiap angka punya (endpoint, field)?",         col=1, row=8)
out   = f.io      ("Output: vonis, 4 paragraf, tabel, daftar sitasi", col=1, row=9)
done  = f.terminal("Pengguna memutuskan sendiri",                 col=1, row=10)

daily = f.store   ("/v2/daily/ · OHLCV 90 hari",                  col=0, row=2)
brok  = f.store   ("broker-summary/top · brokers\n(origin, cohort)", col=0, row=4)
own   = f.store   ("shareholders-composition\nforeign-flow",       col=0, row=5)
news  = f.store   ("/v2/news/?symbols=",                           col=0, row=6)
redo  = f.process ("Ambil ulang field yang tak bersumber",         col=0, row=8)

calm  = f.terminal("Tidak ada anomali · berhenti di sini",         col=2, row=3)
cat   = f.terminal("Ada katalis · turunkan skor, sebut beritanya", col=2, row=6)

lab   = f.store   ("/v2/suspensions/ · 583 label IDX\n'peningkatan harga kumulatif'", col=2, row=0)
ev    = f.subflow ("Evaluasi offline: presisi dan recall pada T-1", col=2, row=1)

n1 = f.note("Ambang 2 SD, jendela t+4 — Nam & Skillicorn 2023", col=2, row=4)
n3 = f.note("P5 · konteks struktural (free-float, suspensi, kapitalisasi) dipakai dengan bobot rendah — Koreksi K1 dan K2", col=0, row=7)
n2 = f.note("Tidak pernah keluar: target harga, sinyal beli/jual, sizing, eksekusi", col=2, row=9)

f.then(s, inp)
f.then(inp, p1)
f.then(p1, d1)
f.branch(d1, yes=p2, no=calm,
         yes_label="Ya · anomali harga dan volume", no_label="Tidak · dalam kebiasaannya")
f.then(p2, p3)
f.then(p3, d2)
f.branch(d2, yes=cat, no=p4,
         yes_label="Ya · pergerakan ada sebabnya", no_label="Tidak · tanpa katalis")
f.then(p4, d3)
f.branch(d3, yes=out, no=redo,
         yes_label="Ya · tiap angka bersitasi", no_label="Tidak · tolak draf")
f.to(redo, p1, "Ambil ulang", ALT,
     exit=T(0.5), entry=L(0.72), corridor=f.corridor(after_col=0))
f.then(out, done)

f.to(daily, p1, "1 kredit", NOTE,
     exit=R(0.5), entry=L(0.28), corridor=f.corridor(after_col=0), dashed=True)
f.to(brok, p2, "2 kredit", NOTE,
     exit=R(0.5), entry=L(0.5), corridor=f.corridor(after_col=0), dashed=True)
f.to(own, p3, "2 kredit", NOTE,
     exit=R(0.5), entry=L(0.5), corridor=f.corridor(after_col=0), dashed=True)
f.to(news, d2, "1 kredit", NOTE,
     exit=R(0.5), entry=L(0.5), corridor=f.corridor(after_col=0), dashed=True)

f.then(lab, ev)
f.to(ev, out, "Angka presisi/recall dilaporkan bersama vonis", NOTE,
     exit=L(0.5), entry=R(0.5), corridor=f.corridor(after_col=1), dashed=True)

f.legend(FLOW,  "alur utama")
f.legend(YES_C, "kondisi terpenuhi")
f.legend(NO_C,  "kondisi gagal · berhenti atau ditolak")
f.legend(ALT,   "pengambilan ulang")
f.legend(NOTE,  "sumber data dan evaluasi", dashed=True)

f.write("research/plan/pump-and-dump/diagrams/alur.drawio")
print("written")
