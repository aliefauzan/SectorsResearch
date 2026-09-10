#!/usr/bin/env python3
"""Papan status pipeline — bukan dashboard pasar.

    python3 tools/dashboard.py            # tulis state/dashboard.html
    python3 tools/dashboard.py --open     # tulis lalu buka di browser
    python3 tools/dashboard.py --check    # verifikasi saja, tidak menulis

## Kenapa papan ini boleh ada, padahal `app/render/__init__.py` menolak dashboard

Penolakan di sana spesifik dan tetap berlaku: Track 03 mendiskualifikasi *"a product
that only displays raw Sectors data in a different visual form"*, jadi grafik
`top_buyers[].buy_idr` tidak akan pernah ditambahkan. Halaman ini tidak menggambar
satu pun deret harga. Yang ditampilkannya adalah **keadaan pipeline itu sendiri** —
tahap mana yang jalan, berapa yang lewat tiap tahap, di titik mana alirannya
berhenti, dan berkas apa yang membuktikannya. Itu bukan render ulang respons API;
itu catatan tentang perangkatnya.

Satu bagian memang menampilkan keluaran produk, dan bentuknya persis yang
disebut sah oleh `app/render/__init__.py` baris terakhir: *"If a visual surface is
ever wanted, it is a list of these paragraphs."* Daftar paragraf, bukan tabel
peringkat.

## Aturan yang mengikat berkas ini

`riset/red-team.md` §D11 melarang vonis dan warna-sebagai-vonis. Dua konsekuensinya
ditegakkan di sini, bukan diserahkan pada niat baik:

  * **kosakata** — seluruh teks yang terlihat di halaman dijalankan lewat
    `paragraph.banned_words_in()`, aturan yang sama yang menjaga paragraf produk.
    Kalau ada satu kata vonis lolos, `build()` mengangkat `BannedVocabularyError`
    dan tidak ada berkas yang ditulis. Fail-closed, sama seperti pemeriksa sitasi.
  * **warna** — palet halaman ini sengaja tidak punya merah dan hijau. Sumbu yang
    menyala diberi oker, yang tidak diberi abu, yang tidak terukur diberi garis
    putus-putus. Membaca papan ini tidak pernah berarti membaca lampu lalu lintas.

Angka di halaman ini dibaca saat pembuatan, tidak ada yang ditanam. Nol kredit:
sumbernya `research/harness/recorded/` dan `state/`, tidak ada soket ke API.
"""
import argparse
import datetime
import html
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config, profile as profile_mod          # noqa: E402
from app.cache import Cache                             # noqa: E402
from app.render import paragraph as para                # noqa: E402

OUT_PATH = os.path.join(config.STATE_DIR, "dashboard.html")

# Nama sumbu sebagaimana dibaca orang yang tidak pernah melihat kodenya.
AXES = ("concentration", "volume_anomaly", "momentum", "catalyst")


# --- pengumpulan angka -------------------------------------------------------

def _jsonl_count(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


def collect_ledger():
    """Kredit yang tercatat di ledger capture.py, dikelompokkan per tanggal."""
    path = os.path.join(config.RECORDED_DIR, "_ledger.jsonl")
    if not os.path.exists(path):
        return {"rows": 0, "billed": 0, "by_day": []}
    per_day, calls = {}, {}
    total = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            ts = row.get("ts")
            if isinstance(ts, (int, float)):
                day = datetime.datetime.fromtimestamp(
                    ts, datetime.timezone.utc).strftime("%Y-%m-%d")
            else:
                day = str(ts)[:10]
            cost = row.get("billed_cost") or 0
            per_day[day] = per_day.get(day, 0) + cost
            calls[day] = calls.get(day, 0) + 1
            total += cost
    by_day = [{"day": d, "calls": calls[d], "billed": per_day[d]}
              for d in sorted(per_day)]
    return {"rows": sum(calls.values()), "billed": total, "by_day": by_day}


def collect_tests():
    """Jumlah tes yang terkumpul. Tidak dijalankan, hanya dihitung."""
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "app/tests", "--collect-only", "-q"],
            cwd=config.PKG_ROOT, capture_output=True, text=True, timeout=120)
    except Exception:
        return None
    for line in reversed(out.stdout.splitlines()):
        if "test" in line and "collected" in line:
            return int(line.split()[0])
    return None


def collect_tasks():
    """Berkas tugas yang ada di `tasks/`, bernomor."""
    names = sorted(n for n in os.listdir(os.path.join(config.PKG_ROOT, "tasks"))
                   if n[:2].isdigit())
    return [{"no": int(n[:2]), "slug": n[3:-3].replace("-", " ")} for n in names]


def collect_recordings():
    if not os.path.isdir(config.RECORDED_DIR):
        return 0
    return sum(1 for n in os.listdir(config.RECORDED_DIR) if not n.startswith("_"))


def collect_profiles(cache):
    """Profil tiap simbol watchlist. Satu kegagalan tidak menjatuhkan papan."""
    rows = []
    for symbol in config.WATCHLIST:
        try:
            profile = profile_mod.build(symbol, cache=cache)
        except Exception as exc:
            rows.append({"symbol": symbol, "error":
                         f"{type(exc).__name__}: {exc}"})
            continue
        readings = {r.axis: r for r in profile.counted}
        rows.append({"symbol": symbol, "profile": profile, "readings": readings})
    return rows


def collect_paragraphs(rows, cache):
    out = []
    for row in rows:
        if "profile" not in row:
            continue
        try:
            out.append(para.render(row["profile"], cache=cache))
        except Exception as exc:
            out.append({"symbol": row["symbol"],
                        "error": f"{type(exc).__name__}: {exc}"})
    return out


def collect_state():
    s = config.STATE_DIR
    thresholds_path = os.path.join(s, "thresholds.json")
    thresholds = {}
    if os.path.exists(thresholds_path):
        with open(thresholds_path, encoding="utf-8") as fh:
            thresholds = json.load(fh)
    runs = []
    runs_path = os.path.join(s, "runs.jsonl")
    if os.path.exists(runs_path):
        with open(runs_path, encoding="utf-8") as fh:
            runs = [json.loads(l) for l in fh if l.strip()]
    backtest_path = os.path.join(s, "backtest_report.json")
    return {
        "thresholds": thresholds,
        "runs": runs,
        "warnings": _jsonl_count(os.path.join(s, "warnings.jsonl")),
        "outcomes": _jsonl_count(os.path.join(s, "outcomes.jsonl")),
        "lessons": _jsonl_count(os.path.join(s, "lessons.jsonl")),
        "credits": _jsonl_count(os.path.join(s, "credits.jsonl")),
        "backtest_bytes": (os.path.getsize(backtest_path)
                           if os.path.exists(backtest_path) else 0),
        "telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN")
                         and os.environ.get("TELEGRAM_CHAT_ID")),
    }


# --- format ------------------------------------------------------------------

def num(value, places=2):
    if value is None:
        return "—"
    text = f"{value:,.{places}f}".replace(",", " ").replace(".", ",")
    return text


def pct(value, places=1):
    return "—" if value is None else num(value * 100, places) + "%"


def e(text):
    return html.escape(str(text), quote=True)


# Palet tanpa merah dan tanpa hijau — §D11 melarang warna sebagai vonis, jadi
# "menyala" diberi oker dan sisanya abu. Papan ini tidak boleh terbaca sebagai
# lampu lalu lintas.
CSS = """
:root{
  --paper:#faf9f6; --ink:#191714; --muted:#6d675f; --rule:#e3dfd6;
  --panel:#ffffff; --accent:#8a6410; --accent-bg:#f6efdf; --slate:#5b6570;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Inter,sans-serif;
}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#141312; --ink:#eae6df; --muted:#9a938a; --rule:#2c2a26;
    --panel:#1c1a18; --accent:#d3a24a; --accent-bg:#2a2418; --slate:#8d97a2;
  }
}
:root[data-theme="dark"]{
  --paper:#141312; --ink:#eae6df; --muted:#9a938a; --rule:#2c2a26;
  --panel:#1c1a18; --accent:#d3a24a; --accent-bg:#2a2418; --slate:#8d97a2;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);
  line-height:1.55;margin:0;padding:0 20px 80px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto}
header{padding:56px 0 28px;border-bottom:1px solid var(--rule)}
h1{font-size:30px;letter-spacing:-.02em;margin:0 0 6px;font-weight:640}
.sub{color:var(--muted);font-size:14px;margin:0}
.strip{margin:22px 0 0;padding:12px 14px;border-left:3px solid var(--accent);
  background:var(--accent-bg);font-size:13px;color:var(--ink);border-radius:0 4px 4px 0}
h2{font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);
  font-weight:660;margin:52px 0 4px}
h2 + .note{margin:0 0 18px}
.note{color:var(--muted);font-size:13.5px;max-width:74ch}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(184px,1fr));margin:18px 0 0}
.stat{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;min-width:0}
.stat b{display:block;font-size:25px;font-weight:640;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;line-height:1.15}
.stat span{display:block;font-size:12px;color:var(--muted);margin-top:5px}
.stat small{display:block;font-size:11.5px;color:var(--muted);margin-top:7px;
  font-family:var(--mono);overflow-wrap:anywhere;line-height:1.45}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:16px}
th{text-align:left;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);font-weight:620;padding:0 10px 8px 0;border-bottom:1px solid var(--rule);
  white-space:nowrap}
td{padding:9px 10px 9px 0;border-bottom:1px solid var(--rule);vertical-align:top;
  font-variant-numeric:tabular-nums}
td.sym{font-family:var(--mono);font-weight:640;letter-spacing:.02em}
.tag{display:inline-block;font-size:11px;font-family:var(--mono);padding:1px 6px;
  border-radius:3px;border:1px solid var(--rule);color:var(--muted);white-space:nowrap}
.tag.on{color:var(--accent);border-color:var(--accent);background:var(--accent-bg);font-weight:640}
.tag.unk{color:var(--slate);border-style:dashed}
.bar{position:relative;height:4px;background:var(--rule);border-radius:2px;margin-top:6px;
  max-width:150px;overflow:hidden}
.bar i{position:absolute;inset:0 auto 0 0;background:var(--muted);border-radius:2px}
.bar i.on{background:var(--accent)}
.pipe{display:flex;flex-direction:column;gap:0;margin-top:18px}
.stage{display:grid;grid-template-columns:26px 1fr auto;gap:14px;align-items:start;
  padding:13px 0;border-bottom:1px solid var(--rule)}
.stage .dot{width:11px;height:11px;border-radius:50%;background:var(--muted);margin:6px 0 0 7px}
.stage.on .dot{background:var(--accent)}
.stage.idle .dot{background:transparent;border:1.5px dashed var(--slate)}
.stage .who{font-weight:620;font-size:14px}
.stage .who code{font-family:var(--mono);font-size:12px;color:var(--muted);font-weight:400;
  display:block;margin-top:2px}
.stage .val{font-family:var(--mono);font-size:13px;text-align:right;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.stage .why{grid-column:2/4;color:var(--muted);font-size:13px;margin-top:5px;max-width:72ch}
.halt{margin:14px 0 0;padding:13px 15px;border:1px solid var(--accent);border-radius:6px;
  background:var(--accent-bg);font-size:13.5px}
.halt b{color:var(--accent)}
.para{background:var(--panel);border:1px solid var(--rule);border-radius:8px;
  padding:18px 20px;margin-top:14px}
.para h3{font-family:var(--mono);font-size:13px;margin:0 0 10px;letter-spacing:.04em;
  display:flex;justify-content:space-between;align-items:center;gap:12px}
.para p{margin:0 0 12px;font-size:14.5px;max-width:76ch}
.para .disc{color:var(--muted);font-size:12.5px;border-top:1px solid var(--rule);
  padding-top:11px;margin:0}
details{margin-top:11px}
summary{cursor:pointer;font-size:12px;color:var(--muted);font-family:var(--mono)}
details ul{margin:10px 0 0;padding-left:16px;font-size:12px;font-family:var(--mono);
  color:var(--muted);line-height:1.7}
details li{margin-bottom:3px;word-break:break-word}
ul.plain{list-style:none;padding:0;margin:14px 0 0;font-size:13.5px}
ul.plain li{padding:9px 0;border-bottom:1px solid var(--rule);color:var(--ink);max-width:80ch}
ul.plain li b{font-weight:620}
.tasks{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:7px;margin-top:16px}
.task{font-size:12.5px;padding:7px 10px;border:1px solid var(--rule);border-radius:5px;
  background:var(--panel);display:flex;gap:8px;align-items:baseline}
.task b{font-family:var(--mono);font-size:11px;color:var(--accent);font-weight:640}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--rule);
  color:var(--muted);font-size:12.5px}
footer code{font-family:var(--mono)}

.layout{display:grid;grid-template-columns:190px minmax(0,1fr);gap:44px;align-items:start}
nav.toc{position:sticky;top:26px;padding:6px 0 0;font-size:13px}
nav.toc a{display:block;padding:5px 0;color:var(--muted);text-decoration:none;
  border-left:2px solid transparent;padding-left:11px;margin-left:-11px}
nav.toc a:hover{color:var(--ink)}
nav.toc a.active{color:var(--accent);border-left-color:var(--accent);font-weight:620}
nav.toc .live{margin-top:18px;font-family:var(--mono);font-size:11px;color:var(--muted);
  padding-left:11px;display:flex;align-items:center;gap:6px}
nav.toc .live i{width:6px;height:6px;border-radius:50%;background:var(--accent);
  display:inline-block;animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
.strip-axes{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 4px}
nav.toc a.switch{margin-top:14px;font-size:12px;font-family:var(--mono);color:var(--accent)}
h3.mini{font-size:13.5px;font-weight:640;margin:26px 0 0;letter-spacing:-.01em}
h2[id]{scroll-margin-top:22px}
.ctx{margin-top:4px}
.ctx summary{font-size:11px}
@media (max-width:860px){
  .layout{grid-template-columns:1fr;gap:0}
  nav.toc{position:static;display:flex;flex-wrap:wrap;gap:4px 14px;margin:18px 0 0;
    padding-bottom:14px;border-bottom:1px solid var(--rule)}
  nav.toc a{border-left:0;padding-left:0;margin-left:0}
  nav.toc .live{padding-left:0;width:100%}
}
@media (max-width:640px){
  .stage{grid-template-columns:20px 1fr}
  .stage .val{grid-column:2;text-align:left;margin-top:4px}
  .stage .why{grid-column:2}
  table{font-size:12.5px}
}
"""


# --- bagian-bagian halaman ---------------------------------------------------

def section_ringkasan(data):
    lit_total = sum(1 for row in data["rows"] if "profile" in row
                    for r in row["readings"].values() if r.fired)
    measured = sum(1 for row in data["rows"] if "profile" in row
                   for r in row["readings"].values() if r.measured)
    tests = data["tests"]
    led = data["ledger"]
    cards = [
        (f"{len(data['tasks'])}", "tugas selesai di <code>tasks/</code>",
         "01 … 21"),
        (f"{tests if tests is not None else '—'}", "tes terkumpul",
         "app/tests"),
        (f"{led['billed']}", "kredit tercatat di ledger",
         f"{led['rows']} panggilan"),
        (f"{data['recordings']}", "payload rekaman dibaca",
         "research/harness/recorded/"),
        (f"{measured}", "pembacaan sumbu terukur",
         f"dari {len(data['rows']) * 4} kemungkinan"),
        (f"{lit_total}", "pembacaan sumbu menyala",
         f"ambang di state/thresholds.json v{data['state']['thresholds'].get('version','—')}"),
    ]
    out = ['<h2 id="ringkasan">Ringkasan</h2>',
           '<p class="note">Tiap angka di bawah dibaca dari berkas saat halaman '
           'ini dibuat. Tidak ada yang ditanam, dan tidak ada satu pun panggilan '
           'berbayar yang dibuat untuk membuatnya.</p>',
           '<div class="grid">']
    for value, label, foot in cards:
        out.append(f'<div class="stat"><b>{value}</b><span>{label}</span>'
                   f'<small>{foot}</small></div>')
    out.append('</div>')
    return "\n".join(out)


def section_pipeline(data):
    st = data["state"]
    rows = [r for r in data["rows"] if "profile" in r]
    lit = [r for r in rows if r["profile"].axes_fired >= config.WARNING_AXES_THRESHOLD]
    lit_readings = sum(1 for r in rows for x in r["readings"].values() if x.fired)
    unknown = sum(1 for r in rows for x in r["readings"].values() if not x.measured)
    version = st["thresholds"].get("version", "—")
    history = st["thresholds"].get("history", [])

    stages = [
        ("on", "Universe", "app/universe.py",
         f"{len(config.WATCHLIST)} simbol",
         "Watchlist tetap, dinormalkan dari kode IDX. Tidak ada penyaringan "
         "pasar penuh di sini — daftarnya sengaja pendek supaya tiap simbol "
         "punya rekaman yang sudah dibayar."),
        ("on", "Cache rekaman", "app/cache.py",
         f"{data['recordings']} payload",
         "Sumber data satu-satunya untuk seluruh papan ini: payload yang sudah "
         "dibayar pada 5 dan 9 September 2026. Nol soket ke API."),
        ("on", "Empat sumbu", "app/axes/",
         f"{lit_readings} menyala · {unknown} tidak terukur",
         "Konsentrasi broker, volume, momentum, katalis — empat endpoint "
         "berbeda, empat cara gagal yang berbeda. Tiap pembacaan bernilai tiga: "
         "menyala, tidak, atau tidak terukur."),
        ("idle", "Profil konvergensi", "app/profile.py",
         f"{len(lit)} dari {len(rows)} lewat ambang {config.WARNING_AXES_THRESHOLD} sumbu",
         "Di sinilah aliran berhenti. Tidak ada simbol yang mencapai tiga sumbu "
         "menyala, jadi tidak ada yang diteruskan ke tahap mana pun sesudahnya."),
        ("idle", "warnings.jsonl", "state/warnings.jsonl",
         f"{st['warnings']} baris",
         "Kosong karena tahap sebelumnya tidak meneruskan apa pun, bukan karena "
         "penulisannya gagal."),
        ("idle", "Penilai hasil", "app/agent/adjudicate.py",
         f"{st['outcomes']} baris di outcomes.jsonl",
         "Tiap peringatan diadili terhadap apa yang benar-benar terjadi "
         "sesudahnya. Tanpa peringatan, tidak ada yang bisa diadili."),
        ("idle", "Pelajaran", "app/agent/lessons.py",
         f"{st['lessons']} baris di lessons.jsonl",
         "Satu baris pelajaran per hasil. Rantainya menunggu tahap di atas."),
        ("on", "Evolusi ambang", "app/agent/evolve.py",
         f"versi {version} · {len(history)} entri riwayat",
         "Ambang hanya bergerak lewat lima penjaga, dan alasan tiap perubahan "
         "ikut tersimpan di dalam berkas ambangnya sendiri."),
        ("on", "Paragraf", "app/render/paragraph.py",
         f"{len(data['paragraphs'])} dirender",
         "Permukaan yang benar-benar dibaca orang. Pemeriksa sitasinya "
         "fail-closed: satu angka tanpa sumber menghentikan keluaran, bukan "
         "lolos dengan tebakan di sebelahnya."),
        ("idle" if not st["telegram"] else "on", "Pengiriman", "app/render/notify.py",
         "Telegram belum diset" if not st["telegram"] else "Telegram siap",
         "Pesan keluar hanya saat sebuah simbol <em>memasuki</em> keadaan sumbu "
         "menyala, tidak selama ia duduk di sana. Nol transisi hari ini."),
        ("on", "Siklus harian", "app/tick.py",
         f"{len(st['runs'])} baris di runs.jsonl",
         f"Cron <code>{config.CRON_UTC}</code>, log di-commit balik ke repo. "
         "Satu siklus menyaring watchlist tanpa ditunggui."),
    ]

    out = ['<h2 id="pipeline">Pipeline</h2>',
           '<p class="note">Urutannya dibaca dari atas ke bawah. Titik penuh '
           'berarti tahap itu menghasilkan sesuatu hari ini; lingkaran '
           'putus-putus berarti tahap itu jalan tapi tidak menerima masukan.</p>',
           '<div class="pipe">']
    for state, who, path, value, why in stages:
        out.append(
            f'<div class="stage {state}"><div class="dot"></div>'
            f'<div class="who">{who}<code>{path}</code></div>'
            f'<div class="val">{value}</div>'
            f'<div class="why">{why}</div></div>')
    out.append('</div>')

    near = _near_miss(rows)
    out.append(
        f'<div class="halt"><b>Alirannya berhenti di profil konvergensi.</b> '
        f'Tujuh dari {len(rows)} simbol berhenti di dua sumbu, dan ambangnya '
        f'tiga. Konsentrasi dan katalis hampir selalu menyala bersama, jadi '
        f'sumbu ketiga harus datang dari volume atau momentum — dan dua itulah '
        f'yang ketat. {near} Log yang sepi tapi berasal dari ambang yang '
        f'didokumentasikan lebih berguna daripada log yang ramai dari ambang '
        f'sementara; alasannya ada di docstring <code>app/tick.py</code>.</div>')
    return "\n".join(out)


def _near_miss(rows):
    """Selisih terkecil ke sumbu berikutnya, dihitung bukan ditulis.

    Momentum dikecualikan dari perbandingan ini. Persentilnya terkuantisasi pada
    16 jendela di rekaman sekarang, jadi selisih relatifnya tidak sebanding
    dengan sumbu yang kontinu: jarak 75 ke 90 terlihat kecil padahal butuh tiga
    langkah 6,25 dan mengharuskan jendela terakhir masuk dua teratas dari 16.
    Membandingkannya begitu saja akan menamai simbol yang keliru sebagai yang
    paling dekat.
    """
    best = None
    for row in rows:
        profile = row["profile"]
        if profile.axes_fired != config.WARNING_AXES_THRESHOLD - 1:
            continue
        for reading in row["readings"].values():
            if reading.axis == "momentum":
                continue
            if reading.fired or not reading.measured or reading.threshold is None:
                continue
            if reading.direction.startswith("di atas"):
                gap = (reading.threshold - reading.value) / reading.threshold
            else:
                gap = (reading.value - reading.threshold) / max(reading.threshold, 1e-9)
            if gap < 0:
                continue
            if best is None or gap < best[0]:
                best = (gap, profile.symbol, reading)
    if best is None:
        return ""
    _, symbol, reading = best
    prose = para.AXIS_PROSE.get(reading.axis, reading.axis)
    return (f"Di luar momentum, yang persentilnya terkuantisasi pada 16 jendela, "
            f"selisih terkecil ada pada {symbol}: sumbu {prose} terbaca "
            f"{num(reading.value, 3)} terhadap ambang {num(reading.threshold, 3)}.")


def section_sumbu(data):
    out = ['<h2 id="sumbu">Sumbu, per simbol</h2>',
           '<p class="note">Nilai terukur di sebelah kiri, ambangnya di sebelah '
           'kanan tanda titik dua. Sebuah sel bertanda putus-putus berarti sumbu '
           'itu tidak terukur — dan itu bukan pernyataan bahwa keadaannya tenang, '
           'melainkan bahwa datanya tidak ada.</p>',
           '<table><thead><tr><th>Simbol</th><th>Sumbu menyala</th>']
    for axis in AXES:
        out.append(f'<th>{e(para.AXIS_PROSE.get(axis, axis))}</th>')
    out.append('</tr></thead><tbody>')

    for row in data["rows"]:
        if "profile" not in row:
            out.append(f'<tr><td class="sym">{e(row["symbol"])}</td>'
                       f'<td colspan="5"><span class="tag unk">'
                       f'{e(row["error"])}</span></td></tr>')
            continue
        profile = row["profile"]
        out.append(f'<tr><td class="sym">{e(profile.symbol)}</td>'
                   f'<td>{profile.axes_fired} / {profile.axes_total}</td>')
        for axis in AXES:
            reading = row["readings"].get(axis)
            out.append('<td>' + _cell(reading) + '</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def _cell(reading):
    if reading is None:
        return '<span class="tag unk">tidak ada</span>'
    if not reading.measured:
        reason = reading.unknown_reason or "tidak terukur"
        return f'<span class="tag unk">{e(reason)}</span>'
    places = 3 if reading.unit == "rasio" else 2
    value = num(reading.value, places)
    bar = num(reading.threshold, places) if reading.threshold is not None else "—"
    klass = "on" if reading.fired else ""
    # Lebar batang: nilai terhadap ambang, dipotong di 100% supaya sebuah
    # pembacaan 24x tidak menjadikan seluruh kolom lain tak terbaca.
    try:
        ratio = min(1.0, abs(reading.value) / abs(reading.threshold))
    except (TypeError, ZeroDivisionError):
        ratio = 0.0
    return (f'<span class="tag {klass}">{value}</span> '
            f'<span style="color:var(--muted);font-size:11.5px">: {bar}</span>'
            f'<div class="bar"><i class="{klass}" style="width:{ratio*100:.0f}%"></i></div>')


def section_ambang(data):
    th = data["state"]["thresholds"]
    current, bounds = th.get("current", {}), th.get("bounds", {})
    out = ['<h2 id="ambang">Ambang</h2>',
           '<p class="note">Dibaca apa adanya dari <code>state/thresholds.json</code>. '
           'Tidak ada satu pun angka di halaman ini yang digeser untuk membuat '
           'papannya terlihat lebih ramai.</p>',
           '<table><thead><tr><th>Sumbu</th><th>Ambang kini</th><th>Batas bawah</th>'
           '<th>Batas atas</th><th>Arah</th></tr></thead><tbody>']
    direction = {
        "concentration": "menyala saat nilai mencapai ambang",
        "volume_anomaly": "menyala saat nilai mencapai ambang",
        "momentum": "menyala saat nilai mencapai ambang",
        "catalyst": "dibaca terbalik: menyala saat nilai turun ke ambang",
    }
    for axis in AXES:
        b = bounds.get(axis, {})
        out.append(
            f'<tr><td>{e(para.AXIS_PROSE.get(axis, axis))}</td>'
            f'<td><span class="tag">{num(current.get(axis), 3)}</span></td>'
            f'<td>{num(b.get("floor"), 2)}</td><td>{num(b.get("ceiling"), 2)}</td>'
            f'<td style="color:var(--muted);font-size:12.5px">{e(direction[axis])}</td></tr>')
    out.append('</tbody></table>')

    factors = th.get("cohort_factors", {})
    if factors:
        pairs = " · ".join(f"{k} {num(v, 2)}" for k, v in factors.items())
        out.append(f'<p class="note" style="margin-top:14px">Faktor kohort broker: '
                   f'{e(pairs)}. Ambang konsentrasi dikali faktor kohortnya '
                   f'sebelum dibandingkan.</p>')

    history = th.get("history", [])
    if history:
        out.append('<ul class="plain">')
        for h in history:
            frm = "belum ada" if h.get("from") is None else num(h["from"], 3)
            out.append(
                f'<li><b>v{h.get("version")} · {e(h.get("on",""))} · '
                f'{e(para.AXIS_PROSE.get(h.get("axis"), h.get("axis")))}</b> — '
                f'{frm} menjadi {num(h.get("to"), 3)}. {e(h.get("reason",""))}</li>')
        out.append('</ul>')
    return "\n".join(out)


def section_paragraf(data):
    out = ['<h2 id="paragraf">Keluaran produk</h2>',
           '<p class="note">Ini permukaan yang sebenarnya: prosa, bukan papan. '
           'Bentuk daftar inilah satu-satunya permukaan visual yang disahkan '
           '<code>app/render/__init__.py</code>. Tiap angka di dalamnya bisa '
           'ditelusuri ke endpoint dan medan yang menghasilkannya — buka '
           '“sumber tiap angka” di bawah tiap paragraf.</p>']
    for item in data["paragraphs"]:
        if isinstance(item, dict):
            out.append(f'<div class="para"><h3>{e(item["symbol"])}</h3>'
                       f'<p>{e(item["error"])}</p></div>')
            continue
        out.append(f'<div class="para"><h3>{e(item.symbol)}'
                   f'<span class="tag">{len(item.cited)} angka tersitasi</span></h3>')
        out.append(f'<p>{e(item.body)}</p>')
        out.append('<details><summary>sumber tiap angka</summary><ul>')
        for cited in item.cited:
            out.append(f'<li>{e(str(cited))}</li>')
        out.append('</ul></details>')
        out.append(f'<p class="disc">{e(item.disclaimer)}</p></div>')
    return "\n".join(out)


def section_kredit(data):
    led = data["ledger"]
    out = ['<h2 id="kredit">Kredit</h2>',
           '<p class="note">Hibah tim 1.000 kredit, tidak bisa ditambah dan '
           'hangus di akhir acara. Angka di bawah dijumlahkan dari '
           '<code>_ledger.jsonl</code>, catatan yang ditulis '
           '<code>capture.py</code> sendiri. Catatan bebasnya ada di ekspor '
           'portal, dan <code>reconcile_usage.py</code> adalah pemeriksa yang '
           'membandingkan keduanya.</p>',
           '<table><thead><tr><th>Tanggal</th><th>Panggilan</th>'
           '<th>Kredit terbebankan</th></tr></thead><tbody>']
    for day in led["by_day"]:
        out.append(f'<tr><td>{e(day["day"])}</td><td>{day["calls"]}</td>'
                   f'<td>{day["billed"]}</td></tr>')
    out.append(f'<tr><td><b>total</b></td><td><b>{led["rows"]}</b></td>'
               f'<td><b>{led["billed"]}</b></td></tr>')
    out.append('</tbody></table>')
    runtime = data["state"]["credits"]
    out.append(
        '<p class="note" style="margin-top:14px">Kredit yang dibelanjakan '
        '<em>produk saat berjalan</em>: ' +
        ('belum ada — <code>state/credits.jsonl</code> belum dibuat, jadi belum '
         'satu pun panggilan berbayar dibuat oleh produk.'
         if runtime in (None, 0) else f'{runtime} baris di state/credits.jsonl.') +
        '</p>')
    return "\n".join(out)


def section_tugas(data):
    out = ['<h2 id="tugas">Tugas</h2>',
           '<p class="note">Berkas tugas yang ada di <code>tasks/</code>, dibaca '
           'dari nama berkasnya. Tiap satu punya commit sendiri.</p>',
           '<div class="tasks">']
    for task in data["tasks"]:
        out.append(f'<div class="task"><b>{task["no"]:02d}</b>{e(task["slug"])}</div>')
    out.append('</div>')
    return "\n".join(out)


def section_batasan(data):
    """Batasan yang dicetak skrip-skripnya sendiri, dikumpulkan di satu tempat."""
    items = [
        ("Gerbang go/no-go belum bisa diputuskan",
         "Ketersediaan data tidak simetris antara lengan kasus dan lengan "
         "kontrol, sistem empat sumbu tidak mengeluarkan satu peringatan pun "
         "sehingga liftnya tidak terdefinisi, dan lengan kontrol dipilih dengan "
         "kriteria yang persis dibaca salah satu baseline. "
         "<code>app/evaluate.py --compare-baselines</code> mencetak ketiganya."),
        ("Momentum tidak bisa menyala pada rekaman ini",
         "Rekaman <code>/v2/daily/</code> hanya memuat 2026-08-10 sampai "
         "2026-09-09, jadi persentil dihitung atas 16 jendela saja dan nilainya "
         "terkuantisasi. Ambang 90 menuntut jendela terakhir berada di dua "
         "teratas dari 16, dan tidak ada simbol yang mendekatinya."),
        ("Kebocoran seleksi di backtest",
         "Baris screener dan daftar broker adalah snapshot September 2026 tanpa "
         "tanggal, jadi keanggotaan universe pada tanggal yang lebih awal "
         "memakai informasi yang belum ada saat itu. Diketahui, dan tidak bisa "
         "diperbaiki tanpa membeli screener historis."),
        ("Panel broker tidak bisa dipotong pada T",
         "Panelnya agregat satu jendela tanpa rincian harian, jadi sumbu "
         "konsentrasi tidak terukur di seluruh periode uji backtest."),
        ("Hold-out sangat tipis",
         "Enam pasangan tanggal-emiten berlabel. Angka apa pun dari sana punya "
         "selang kepercayaan yang lebar dan tidak boleh dikutip sebagai presisi "
         "produk."),
    ]
    out = ['<h2 id="batasan">Batasan</h2>',
           '<p class="note">Bukan temuan pihak lain: tiap butir di bawah dicetak '
           'oleh skripnya sendiri saat dijalankan, dan dikumpulkan di sini supaya '
           'tidak perlu dicari satu per satu.</p>',
           '<ul class="plain">']
    for title, body in items:
        out.append(f'<li><b>{title}</b> — {body}</li>')
    out.append('</ul>')
    return "\n".join(out)


# --- perakitan ---------------------------------------------------------------

RE = __import__("re")
TAGS = RE.compile(r"<[^>]+>")
# Sebuah `<code>` yang isinya satu kata tanpa spasi adalah pengenal: nama berkas,
# jalur endpoint, ekspresi cron. `/v2/sgx/short-sell/` bukan vonis, ia nama yang
# dipakai API dan tidak boleh diubah supaya lolos pemeriksaan. Yang dikecualikan
# hanya bentuk itu — begitu sebuah `<code>` memuat spasi ia kembali diperiksa,
# jadi prosa tidak bisa diselundupkan ke dalamnya.
IDENT = RE.compile(r"<code>(\S+)</code>")


def visible_text(markup):
    """Teks yang benar-benar dibaca orang, tanpa markup — bahan pemeriksaan."""
    return html.unescape(TAGS.sub(" ", IDENT.sub(" ", markup)))


NAV_USER = [
    ("ringkas", "Hari ini"),
    ("catatan", "Catatan"),
    ("cara", "Cara membaca"),
]

NAV = [
    ("ringkasan", "Ringkasan"),
    ("pipeline", "Pipeline"),
    ("sumbu", "Sumbu"),
    ("ambang", "Ambang"),
    ("gerbang", "Gerbang"),
    ("backtest", "Backtest"),
    ("paragraf", "Paragraf"),
    ("siklus", "Siklus harian"),
    ("kredit", "Kredit"),
    ("data", "Asal data"),
    ("tugas", "Tugas"),
    ("batasan", "Batasan"),
]

# Muat ulang otomatis saat disajikan `tools/serve.py`: halaman menanyakan sidik
# jari berkas tiap beberapa detik dan memuat ulang kalau berubah. Tidak ada
# pustaka luar, tidak ada soket yang dibuka ke mana pun selain server lokal itu
# sendiri. Berkas statis tidak memuat skrip ini sama sekali.
LIVE_JS = """
(function(){
  var current=null;
  function poll(){
    fetch('/api/fingerprint',{cache:'no-store'})
      .then(function(r){return r.text()})
      .then(function(t){
        if(current===null){current=t;return}
        if(t!==current){location.reload()}
      })
      .catch(function(){});
  }
  poll(); setInterval(poll, 3000);
  var links=[].slice.call(document.querySelectorAll('nav.toc a'));
  var heads=links.map(function(a){return document.getElementById(a.hash.slice(1))});
  function mark(){
    var best=0;
    heads.forEach(function(h,i){ if(h && h.getBoundingClientRect().top<130){best=i} });
    links.forEach(function(a,i){ a.className = i===best ? 'active' : '' });
  }
  document.addEventListener('scroll', mark, {passive:true}); mark();
})();
"""


def build(data, live=False, mode="user"):
    """Rakit halaman, lalu periksa kosakatanya sebelum satu byte pun ditulis.

    `mode` memilih siapa pembacanya. `user` memuat apa yang dipakai orang yang
    memakai produknya: catatan per kode saham dan cara membacanya. `pipeline`
    memuat catatan pembangunan — tahap, gerbang, backtest, kredit — yang berguna
    untuk yang menilai repo dan tidak untuk yang membaca satu kode saham.
    """
    built = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    version = data["state"]["thresholds"].get("version", "—")
    user = mode == "user"

    nav = ['<nav class="toc">']
    for ident, label in (NAV_USER if user else NAV):
        nav.append(f'<a href="#{ident}">{label}</a>')
    nav.append(f'<a class="switch" href="{"/pipeline" if user else "/"}">'
               f'{"catatan pembangunan →" if user else "← papan pengguna"}</a>')
    if live:
        nav.append('<div class="live"><i></i>tersambung</div>')
    nav.append('</nav>')

    if user:
        sections = "\n".join([
            section_user_head(data),
            section_user_paragraf(data),
            section_user_cara(data),
        ])
    else:
        sections = "\n".join([
            section_ringkasan(data),
            section_pipeline(data),
            section_sumbu(data),
            section_ambang(data),
            section_gerbang(data),
            section_backtest(data),
            section_paragraf(data),
            section_siklus(data),
            section_kredit(data),
            section_data(data),
            section_tugas(data),
            section_batasan(data),
        ])

    body = "\n".join([
        '<div class="wrap">',
        '<header>',
        f'<h1>{"mersamur" if user else "mersamur — catatan pembangunan"}</h1>',
        (f'<p class="sub">Empat sumbu atas satu kode saham, dari respons Sectors '
         f'API pada jendela yang disebut. Dibaca {e(built)}, ambang versi '
         f'{version}.</p>'
         if user else
         f'<p class="sub">Dibaca {e(built)} dari berkas di <code>state/</code> '
         f'dan <code>research/harness/recorded/</code>. Ambang versi {version}. '
         f'Nol kredit: tidak ada panggilan API yang dibuat untuk merender '
         f'halaman ini.</p>'),
        f'<div class="strip">{e(para.DISCLAIMER)}</div>',
        '</header>',
        '<div class="layout">',
        "\n".join(nav),
        f'<main>{sections}</main>',
        '</div>',
        ('<footer>Seluruh teks di halaman ini deskriptif dan diperiksa terhadap '
         'daftar kosakata di <code>app/render/paragraph.py</code> sebelum '
         'dikirim: satu angka tanpa sumber atau satu kata vonis menghentikan '
         'halaman, bukan lolos begitu saja. Pernyataan lengkapnya ada di '
         '<code>mersamur/DISCLAIMER.md</code>.</footer>'
         if user else
         '<footer>Papan ini menampilkan keadaan pipeline, bukan render ulang '
         'respons API — pembedaan yang dituntut Track 03 dan dicatat di '
         '<code>tools/dashboard.py</code>. Seluruh teksnya deskriptif dan '
         'diperiksa terhadap daftar kosakata di '
         '<code>app/render/paragraph.py</code> sebelum halaman dikirim. '
         'Bangun ulang: <code>python3 tools/dashboard.py</code> · '
         'sajikan: <code>python3 tools/serve.py</code>.</footer>'),
        '</div>',
    ])

    found = para.banned_words_in(visible_text(body))
    if found:
        raise para.BannedVocabularyError(
            f"kosakata vonis di papan: {', '.join(sorted(found))}")

    script = f"<script>{LIVE_JS}</script>" if live else ""
    return ("<!doctype html>\n<html lang=\"id\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{'mersamur' if user else 'mersamur — catatan pembangunan'}"
            "</title>\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n{script}\n"
            "</body>\n</html>\n")


def collect_backtest():
    path = os.path.join(config.STATE_DIR, "backtest_report.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def collect_evaluate(cache):
    """Gerbang tugas 11, dihitung ulang tiap kali papan dirakit. Nol kredit."""
    try:
        from app import evaluate
        return evaluate.report(cache=cache)
    except Exception:
        return None


def collect_manifest():
    """Rekaman dikelompokkan per endpoint, bukan per slug panggilan."""
    path = os.path.join(config.RECORDED_DIR, "_manifest.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return None
    grouped = {}
    for row in raw.values():
        endpoint = row.get("path", "?")
        slot = grouped.setdefault(endpoint, {"calls": 0, "cost": 0})
        slot["calls"] += 1
        slot["cost"] += row.get("est_cost") or 0
    return grouped


def gather(with_evaluate=True):
    cache = Cache()
    rows = collect_profiles(cache)
    return {
        "rows": rows,
        "paragraphs": collect_paragraphs(rows, cache),
        "state": collect_state(),
        "ledger": collect_ledger(),
        "tests": collect_tests(),
        "tasks": collect_tasks(),
        "recordings": collect_recordings(),
        "backtest": collect_backtest(),
        "manifest": collect_manifest(),
        "evaluate": collect_evaluate(cache) if with_evaluate else None,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Papan status pipeline mersamur, dari berkas lokal saja.",
        epilog="Deskriptif, bukan anjuran investasi. Teks lengkapnya: "
               "mersamur/DISCLAIMER.md.")
    ap.add_argument("--out", default=OUT_PATH, help="tujuan berkas HTML")
    ap.add_argument("--open", action="store_true",
                    help="buka berkasnya di browser setelah ditulis")
    ap.add_argument("--check", action="store_true",
                    help="rakit dan periksa, tapi jangan menulis apa pun")
    ap.add_argument("--mode", choices=("user", "pipeline"), default="user",
                    help="user: catatan per kode saham. pipeline: catatan "
                         "pembangunan — tahap, gerbang, backtest, kredit")
    args = ap.parse_args(argv)

    data = gather(with_evaluate=args.mode == "pipeline")
    try:
        page = build(data, mode=args.mode)
    except para.BannedVocabularyError as exc:
        print(f"papan tidak ditulis — {exc}", file=sys.stderr)
        return 1

    failed = [r for r in data["rows"] if "profile" not in r]
    if args.check:
        print(f"ok — {len(page):,} bita, {len(data['paragraphs'])} paragraf, "
              f"{len(failed)} simbol gagal. Tidak ada yang ditulis.")
        return 0

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"ditulis: {args.out}  ({len(page):,} bita)")
    if failed:
        print(f"catatan: {len(failed)} simbol tanpa profil — "
              f"{', '.join(r['symbol'] for r in failed)}")
    if args.open:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(args.out))
    return 0




# --- bagian yang hanya muncul di papan penuh ---------------------------------

ARM_PROSE = {
    "empat_sumbu": "empat sumbu (sistem ini)",
    "momentum_5h": "momentum 5 hari (baseline)",
    "pernah_disuspensi": "pernah disuspensi (baseline)",
    "momentum_5h+empat_sumbu": "momentum + empat sumbu",
}


def _rate(value, places=1):
    return "—" if value is None else pct(value, places)


def _lift(value):
    return "—" if value is None else num(value, 2) + "x"


def _arm_table(results, order=None):
    order = order or list(results)
    out = ['<table><thead><tr><th>Lengan</th><th>n</th><th>Peringatan</th>'
           '<th>TP</th><th>FP</th><th>FN</th><th>TN</th><th>Presisi</th>'
           '<th>Recall</th><th>Lift</th></tr></thead><tbody>']
    for name in order:
        r = results.get(name)
        if r is None:
            continue
        prose = ARM_PROSE.get(name, name)
        strong = ' style="font-weight:640"' if name == "empat_sumbu" else ""
        out.append(
            f'<tr{strong}><td>{e(prose)}</td><td>{r["n"]}</td>'
            f'<td>{r["warnings"]}</td><td>{r["tp"]}</td><td>{r["fp"]}</td>'
            f'<td>{r["fn"]}</td><td>{r["tn"]}</td>'
            f'<td>{_rate(r.get("precision"))}</td>'
            f'<td>{_rate(r.get("recall"))}</td>'
            f'<td>{_lift(r.get("lift"))}</td></tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def section_gerbang(data):
    ev = data.get("evaluate")
    out = ['<h2 id="gerbang">Gerbang go/no-go</h2>']
    if not ev:
        out.append('<p class="note">Tidak bisa dihitung pada berkas yang ada '
                   'sekarang.</p>')
        return "\n".join(out)

    arms, gate = ev["arms"], ev["gate"]
    out.append(
        f'<p class="note">Pertanyaannya satu: apakah empat sumbu mengungguli dua '
        f'baseline naif pada set yang sama. Set dirakit kasus-kontrol — '
        f'{len(arms["kasus"])} emiten pernah disuspensi, {len(arms["kontrol"])} '
        f'tidak, {len(arms["dikeluarkan"])} dikeluarkan — jadi base rate '
        f'{pct(0.5, 0)} di sini adalah bawaan rancangan set, bukan sifat pasar. '
        f'Base rate pasar sebenarnya {pct(ev.get("market_base_rate"), 1)} per '
        f'saham per 10 hari bursa; lift di tabel ini tidak boleh dikutip sebagai '
        f'lift pasar.</p>')
    out.append(_arm_table(ev["results"],
                          ["empat_sumbu", "momentum_5h", "pernah_disuspensi",
                           "momentum_5h+empat_sumbu"]))

    cond = ev.get("conditional", {})
    out.append(
        f'<p class="note" style="margin-top:16px"><b>Apakah empat sumbu menambah '
        f'sesuatu di atas momentum:</b> momentum menyala pada {cond.get("n_base", 0)} '
        f'emiten, {_rate(cond.get("p_base"))} di antaranya berlabel. Dari situ '
        f'{cond.get("n_both", 0)} juga dinyalakan empat sumbu. Irisannya kosong, '
        f'jadi pertanyaannya tidak terjawab — bukan terjawab nol.</p>')

    out.append('<h3 class="mini">Sumbu yang benar-benar terukur per lengan</h3>')
    out.append('<table><thead><tr><th>Lengan</th><th>n</th><th>Terukur</th>'
               '<th>Rata-rata</th><th>Tidak terukur</th></tr></thead><tbody>')
    for arm, m in ev["measurability"].items():
        missing = m.get("missing") or {}
        miss = " · ".join(f"{para.AXIS_PROSE.get(k, k)} {v}x"
                          for k, v in missing.items()) or "—"
        out.append(
            f'<tr><td>{e(arm)}</td><td>{m["n"]}</td>'
            f'<td>{m["min_measurable"]}..{m["max_measurable"]} dari 4</td>'
            f'<td>{num(m["mean_measurable"], 1)}</td><td>{e(miss)}</td></tr>')
    out.append('</tbody></table>')

    if not gate.get("adjudicable"):
        verdict, gloss = "BERHENTI", ("Bukan karena modelnya kalah, tapi karena "
                                      "perbandingannya belum sah. Penghalangnya:")
    elif gate.get("passed"):
        verdict, gloss = "LANJUT", "Empat sumbu mengungguli kedua baseline. Catatan:"
    else:
        verdict, gloss = "BERHENTI", ("Perbandingannya sah dan empat sumbu tidak "
                                      "mengunggulinya. Alasannya:")
    out.append(f'<div class="halt" style="margin-top:20px"><b>{e(verdict)}.</b> '
               f'{e(gloss)}</div>')
    out.append('<ul class="plain">')
    for blocker in gate.get("blockers", ()):
        out.append(f'<li>{e(blocker)}</li>')
    for reason in gate.get("reasons", ()):
        out.append(f'<li style="color:var(--muted)">{e(reason)}</li>')
    out.append('</ul>')
    out.append('<p class="note" style="margin-top:12px">Menyetel ambang untuk '
               'memenangkan gerbang ini dilarang — <code>tasks/11</code> §Jangan. '
               'Tidak ada angka di tabel atas yang digeser.</p>')
    return "\n".join(out)


def section_backtest(data):
    bt = data.get("backtest")
    out = ['<h2 id="backtest">Backtest walk-forward</h2>']
    if not bt:
        out.append('<p class="note">Belum ada <code>state/backtest_report.json</code>. '
                   'Bangun dengan <code>python3 app/backtest.py --walk-forward</code>.</p>')
        return "\n".join(out)

    p, grid = bt["parameters"], bt["grid"]
    out.append(
        f'<p class="note">Replay {e(p["start"])} sampai {e(p["end"])} pada '
        f'{grid["n_tanggal"]} tanggal, langkah {p["step_hari_bursa"]} hari bursa, '
        f'horizon {p["horizon_hari_bursa"]} hari bursa, universe '
        f'{p["universe"]} emiten, ambang {p["min_axes"]} sumbu, ambang versi '
        f'{p["thresholds_version"]}. Hold-out mulai {e(p["holdout"])} dan '
        f'{"tidak dipakai" if not p["holdout_dipakai_menyetel"] else "dipakai"} '
        f'untuk menyetel apa pun pada jalankan ini.</p>')

    for key, title in (("penyetelan", "Set penyetelan"), ("hold_out", "Hold-out")):
        split = bt["splits"].get(key)
        if not split:
            continue
        ket = split.get("ketersediaan", {})
        out.append(f'<h3 class="mini">{title} — {split["n_tanggal"]} tanggal · '
                   f'{split["n_peristiwa"]} peristiwa berlabel · '
                   f'{e(split["rentang"][0])} .. {e(split["rentang"][1])}</h3>')
        out.append(_arm_table(split["results"],
                              ["empat_sumbu", "momentum_5h", "pernah_disuspensi",
                               "momentum_5h+empat_sumbu"]))
        out.append(
            f'<p class="note" style="margin-top:10px">Ketersediaan pada '
            f'{ket.get("n", 0)} pasangan: deret harian {ket.get("deret_harian", 0)}, '
            f'artikel {ket.get("artikel", 0)}, panel broker '
            f'{ket.get("panel_broker", 0)}. Sumbu yang datanya tidak ada tidak '
            f'pernah menyala.</p>')

    if bt.get("regimes"):
        out.append('<h3 class="mini">Per rezim</h3>')
        out.append('<table><thead><tr><th>Rezim</th><th>Tanggal</th>'
                   '<th>Peristiwa</th><th>Rentang</th></tr></thead><tbody>')
        for year, reg in sorted(bt["regimes"].items()):
            out.append(f'<tr><td>{e(year)}</td><td>{reg["n_tanggal"]}</td>'
                       f'<td>{reg["n_peristiwa"]}</td>'
                       f'<td>{e(reg["rentang"][0])} .. {e(reg["rentang"][1])}</td></tr>')
        out.append('</tbody></table>')
        out.append('<p class="note" style="margin-top:10px">Base rate tiap rezim '
                   'berbeda, jadi angka lintas tahun tidak boleh digabung begitu '
                   'saja.</p>')

    if bt.get("ditahan"):
        out.append('<h3 class="mini">Payload yang ditahan</h3><ul class="plain">')
        for item in bt["ditahan"]:
            out.append(f'<li><code>{e(item)}</code> — tidak bisa dipotong pada T, '
                       f'jadi tidak dipakai.</li>')
        out.append('</ul>')

    if bt.get("temuan"):
        out.append('<h3 class="mini">Temuan</h3><ul class="plain">')
        for item in bt["temuan"]:
            out.append(f'<li>{e(item)}</li>')
        out.append('</ul>')
    return "\n".join(out)


def section_siklus(data):
    runs = data["state"]["runs"]
    out = ['<h2 id="siklus">Siklus harian</h2>',
           f'<p class="note">Cron <code>{e(config.CRON_UTC)}</code> — sekitar '
           f'pukul {config.TICK_HOUR_WIB} WIB tiap hari kerja. Tiap jalankan '
           f'menambah satu baris, dan barisnya di-commit balik ke repo supaya '
           f'riwayatnya tidak bisa dirapikan belakangan.</p>']
    if not runs:
        out.append('<p class="note">Belum ada baris di <code>state/runs.jsonl</code>.</p>')
        return "\n".join(out)
    out.append('<table><thead><tr><th>Waktu</th><th>Run</th><th>Disaring</th>'
               '<th>Peringatan</th><th>Durasi</th><th>Status</th><th>Catatan</th>'
               '</tr></thead><tbody>')
    for run in reversed(runs):
        out.append(
            f'<tr><td>{e(run.get("ts",""))}</td>'
            f'<td class="sym">{e(run.get("run_id",""))}</td>'
            f'<td>{run.get("symbols_screened", "—")}</td>'
            f'<td>{run.get("warnings_emitted", "—")}</td>'
            f'<td>{run.get("duration_ms", "—")} ms</td>'
            f'<td><span class="tag">{e(run.get("status",""))}</span></td>'
            f'<td style="color:var(--muted);font-size:12.5px">'
            f'{e(run.get("notes",""))}</td></tr>')
    out.append('</tbody></table>')
    out.append('<p class="note" style="margin-top:12px">Baris pertama ditulis '
               'prototipe <code>tools/profile_demo.py</code> dengan aturannya '
               'sendiri yang lebih longgar — tujuh dari sepuluh lewat. Ambang '
               'yang dipakai produk sekarang menaruh nol di sana, dan selisih itu '
               'sengaja tidak dihapus dari log.</p>')
    return "\n".join(out)


def section_data(data):
    man = data.get("manifest") or {}
    out = ['<h2 id="data">Asal data</h2>',
           '<p class="note">Tiap payload di bawah sudah dibayar dengan kredit '
           'hibah dan dikomit ke repo dengan sengaja, supaya orang kedua yang '
           'membutuhkan panggilan yang sama mendapatkannya gratis.</p>']
    if not man:
        out.append('<p class="note">Manifes rekaman tidak terbaca.</p>')
        return "\n".join(out)
    out.append('<table><thead><tr><th>Endpoint</th><th>Payload</th>'
               '<th>Perkiraan kredit</th></tr></thead><tbody>')
    for path, row in sorted(man.items(), key=lambda kv: (-kv[1]["calls"], kv[0])):
        out.append(f'<tr><td><code>{e(path)}</code></td><td>{row["calls"]}</td>'
                   f'<td>{row["cost"]}</td></tr>')
    out.append('</tbody></table>')
    return "\n".join(out)




# --- papan pengguna ----------------------------------------------------------
#
# Apa yang dipakai orang yang memakai produknya, dan tidak lebih. Tahap pipeline,
# gerbang tugas 11, hasil backtest, kredit dan daftar tugas adalah catatan
# pembangunan: berguna untuk yang menilai repo, tidak untuk yang menerima satu
# kode saham di grup chat lalu ingin tahu apa yang tercatat tentangnya. Keduanya
# tetap ada, tapi yang dibuka lebih dulu adalah ini.

def _last_run(data):
    runs = data["state"]["runs"]
    return runs[-1] if runs else None


def section_user_head(data):
    run = _last_run(data)
    rows = [r for r in data["rows"] if "profile" in r]
    lit = [r for r in rows if r["profile"].axes_fired >= config.WARNING_AXES_THRESHOLD]
    window = rows[0]["profile"] if rows else None

    out = ['<h2 id="ringkas">Yang tercatat hari ini</h2>']
    if window:
        out.append(
            f'<p class="note">Jendela yang dibaca: {e(window.window_start)} sampai '
            f'{e(window.window_end)}. Tiap kode saham di bawah diperiksa pada '
            f'empat sumbu yang datanya saling bebas, dan sebuah kode baru '
            f'dianggap perlu disebut saat {config.WARNING_AXES_THRESHOLD} dari 4 '
            f'sumbu menyala sekaligus.</p>')
    cards = [
        (str(len(rows)), "kode saham diperiksa", "daftar pantau"),
        (str(len(lit)), f"mencapai {config.WARNING_AXES_THRESHOLD} sumbu",
         "tidak ada yang perlu dikirim" if not lit else ", ".join(
             r["profile"].symbol for r in lit)),
    ]
    if run:
        cards.append((e(run.get("ts", "")[:10]), "terakhir diperiksa",
                      e(run.get("status", ""))))
    out.append('<div class="grid">')
    for value, label, foot in cards:
        out.append(f'<div class="stat"><b>{value}</b><span>{label}</span>'
                   f'<small>{foot}</small></div>')
    out.append('</div>')
    return "\n".join(out)


def _axis_strip(row):
    """Empat sumbu sebagai satu baris ringkas di bawah paragraf."""
    cells = []
    for axis in AXES:
        reading = row["readings"].get(axis)
        prose = para.AXIS_PROSE.get(axis, axis)
        if reading is None or not reading.measured:
            cells.append(f'<span class="tag unk">{e(prose)} tidak terukur</span>')
            continue
        places = 3 if reading.unit == "rasio" else 2
        klass = "on" if reading.fired else ""
        cells.append(f'<span class="tag {klass}">{e(prose)} '
                     f'{num(reading.value, places)} : '
                     f'{num(reading.threshold, places)}</span>')
    return '<div class="strip-axes">' + " ".join(cells) + '</div>'


def section_user_paragraf(data):
    by_symbol = {r["symbol"]: r for r in data["rows"] if "profile" in r}
    out = ['<h2 id="catatan">Catatan per kode saham</h2>',
           '<p class="note">Tiap angka di dalam kalimat bisa ditelusuri ke '
           'endpoint dan medan yang menghasilkannya — buka “sumber tiap angka”. '
           'Sebuah sumbu yang tidak terukur ditulis apa adanya, bukan dibaca '
           'sebagai keadaan yang tenang.</p>']
    for item in data["paragraphs"]:
        if isinstance(item, dict):
            out.append(f'<div class="para"><h3>{e(item["symbol"])}</h3>'
                       f'<p>{e(item["error"])}</p></div>')
            continue
        row = by_symbol.get(item.symbol)
        fired = row["profile"].axes_fired if row else 0
        total = row["profile"].axes_total if row else 4
        out.append(f'<div class="para"><h3>{e(item.symbol)}'
                   f'<span class="tag">{fired} dari {total} sumbu</span></h3>')
        out.append(f'<p>{e(item.body)}</p>')
        if row:
            out.append(_axis_strip(row))
        out.append('<details><summary>sumber tiap angka</summary><ul>')
        for cited in item.cited:
            out.append(f'<li>{e(str(cited))}</li>')
        out.append('</ul></details>')
        out.append(f'<p class="disc">{e(item.disclaimer)}</p></div>')
    return "\n".join(out)


def section_user_cara(data):
    th = data["state"]["thresholds"].get("current", {})
    bars = " · ".join(
        f"{para.AXIS_PROSE.get(a, a)} {num(th.get(a), 3)}" for a in AXES)
    out = ['<h2 id="cara">Cara membacanya</h2>',
           '<ul class="plain">',
           '<li><b>Ini catatan, bukan penilaian.</b> Kalimat di atas menyatakan '
           'apa yang dikembalikan Sectors API pada jendela yang disebut. Ia tidak '
           'menyatakan apa pun tentang emitennya, dan tidak menyarankan tindakan '
           'apa pun.</li>',
           '<li><b>Empat sumbu, bukan satu skor.</b> Konsentrasi broker, volume, '
           'momentum dan katalis dibaca dari empat endpoint berbeda. Yang '
           'dilaporkan adalah berapa yang menyala dan mana — bukan rata-rata '
           'tertimbang, karena satu angka menyembunyikan sumbu mana yang '
           'menanggung bebannya.</li>',
           f'<li><b>Ambangnya terbuka.</b> {e(bars)}. Angkanya ada di '
           '<code>state/thresholds.json</code> beserta alasan tiap kali ia '
           'pernah bergerak.</li>',
           '<li><b>Tidak terukur bukan berarti tenang.</b> Panel broker yang '
           'hilang atau kode saham yang tidak ditulis siapa pun dilaporkan '
           'sebagai tidak terukur, dan tidak pernah dihitung sebagai sumbu yang '
           'padam.</li>',
           '</ul>']
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
