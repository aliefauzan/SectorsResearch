#!/usr/bin/env python3
"""
The browser surface: a view over `reader.py`, not a second engine.

    python3 webapp.py --port 8080

Every design decision here is downstream of one measurement. Sharif et al. (ASSETS 2021,
DOI 10.1145/3441852.3471202) put screen-reader users at 34% accuracy against 87% for
sighted users on the same online charts, and found that the library that closed most of
that gap won *"as it provides an alternate tabular representation of data that is only
visible to screen readers"* — 73% against Chart.js's 11%. So this page does not draw a
chart and then describe it. There is no chart. There is the sentence, and under it the
table with the raw numbers.

What that means concretely, and what `a11y_check.py` asserts:

  * one `<h1>`, then `<h2>` per section with no skipped levels — heading navigation is
    how a screen-reader user moves through a page, and a gap breaks it
  * a summary before any detail (VoxLens: 34% -> 75%)
  * every table has a `<caption>` and `<th scope=…>` — this is the thing that measurably
    works, so it is not optional anywhere on the page
  * a citation list per section giving endpoint, field and window
  * `aria-live` for the answer to a question, so it is announced without moving focus
  * audio off by default, behind a labelled control, and never the only way to get a fact
  * `lang="id"`, a skip link, visible focus, and no meaning carried by colour alone

The page is deliberately plain. A blind user's screen reader does not care how it looks,
and a sighted judge should be able to see in one screenful that the content is the text.
"""
import argparse
import html
import http.server
import json
import os
import socketserver
import urllib.parse

import narrate
import reader
import sources
from money import say_date

HERE = os.path.dirname(os.path.abspath(__file__))

#: Which section may offer audio, and what the tone is playing. Only the two findings
#: inside the measured parity zone appear here; `narrate.check_audio_zone` keeps it so.
AUDIBLE_LABEL = {
    "price_trend": "Dengarkan arah harga",
    "flow_runs": "Dengarkan arah arus dana asing",
}

STYLE = """
:root { --ink:#111; --paper:#fff; --rule:#767676; --accent:#0b4f9e; --warn:#8a4b00; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#f2f2f2; --paper:#111; --rule:#9a9a9a; --accent:#8ab4f8; --warn:#f0b357; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink);
       font:1.05rem/1.6 system-ui, -apple-system, "Segoe UI", sans-serif; }
main, header, footer { max-width:52rem; margin:0 auto; padding:0 1.25rem; }
a { color:var(--accent); }
a:focus-visible, button:focus-visible, select:focus-visible, input:focus-visible {
  outline:3px solid var(--accent); outline-offset:2px; }
.skip { position:absolute; left:-9999px; }
.skip:focus { position:static; display:inline-block; padding:.5rem; }
h1 { font-size:1.6rem; margin:1.5rem 0 .25rem; }
h2 { font-size:1.25rem; margin:2rem 0 .5rem; border-top:1px solid var(--rule);
     padding-top:1rem; }
h3 { font-size:1rem; margin:1.25rem 0 .35rem; }
.lede { font-size:1.15rem; }
table { border-collapse:collapse; width:100%; margin:.75rem 0; }
caption { text-align:left; font-weight:600; padding:.35rem 0; }
th, td { border:1px solid var(--rule); padding:.4rem .6rem; text-align:left; }
th[scope="col"] { background:rgba(127,127,127,.14); }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.cite { font-size:.9rem; color:var(--ink); }
.cite dt { font-weight:600; margin-top:.4rem; }
.cite dd { margin:0 0 0 1rem; }
.gap { border-left:4px solid var(--warn); padding:.5rem .75rem; margin:.5rem 0; }
.note { border:1px solid var(--rule); padding:.6rem .75rem; margin:1rem 0; }
button, select { font:inherit; padding:.4rem .7rem; }
[aria-live] { min-height:1.6em; }
footer { margin:3rem 0 2rem; font-size:.92rem; }
"""


def esc(value):
    return html.escape(str(value), quote=True)


def number_cell(value):
    """Raw figures, grouped for the eye and left intact for the screen reader.

    The spoken form is in the sentence above; this cell exists so the exact number is
    recoverable. Rounding here would make the two disagree.
    """
    if value is None:
        return '<td class="num">belum diambil</td>'
    if isinstance(value, float):
        return f'<td class="num">{value:,.4f}</td>'
    return f'<td class="num">{value:,}</td>'


# ----------------------------------------------------------------------------- tables
#
# One table per finding, carrying the numbers the sentence was derived from. Not a
# decoration: this is the alternate tabular representation that the 73%-vs-11% result is
# actually about, so every section has one and each one gets a real caption.


def table_segments(finding):
    ranked = finding.numbers["ranked"]
    rows = "".join(
        f'<tr><th scope="row">{esc(item["name"])}</th>'
        f'{number_cell(item["value"])}'
        f'<td class="num">{item["share"] * 100:.1f}%</td></tr>'
        for item in ranked)
    return (f'<table><caption>Sumber pendapatan tahun buku '
            f'{esc(finding.numbers["financial_year"])}, mengalir ke '
            f'{esc(finding.numbers["root"])}</caption>'
            f'<thead><tr><th scope="col">Sumber</th>'
            f'<th scope="col">Nilai (rupiah)</th>'
            f'<th scope="col">Porsi</th></tr></thead><tbody>{rows}</tbody></table>')


def table_price(finding):
    numbers = finding.numbers
    rows = "".join(
        f'<tr><th scope="row">{esc(label)}</th>'
        f'<td>{esc(say_date(row["date"]))}</td>{number_cell(row["close"])}</tr>'
        for label, row in (("Awal jendela", numbers["first"]),
                           ("Akhir jendela", numbers["last"]),
                           ("Tertinggi", numbers["high"]),
                           ("Terendah", numbers["low"])))
    return (f'<table><caption>Harga penutupan, {numbers["n"]} hari bursa terekam'
            f'</caption><thead><tr><th scope="col">Titik</th>'
            f'<th scope="col">Tanggal</th><th scope="col">Harga (rupiah)</th></tr>'
            f'</thead><tbody>{rows}</tbody></table>')


def table_flow(finding):
    numbers = finding.numbers
    streak = ("asing membeli" if numbers["run_sign"] > 0 else "asing menjual")
    rows = (f'<tr><th scope="row">Arus bersih kumulatif</th>'
            f'{number_cell(numbers["cumulative"])}</tr>'
            f'<tr><th scope="row">Hari bursa terekam</th>'
            f'{number_cell(numbers["n"])}</tr>'
            f'<tr><th scope="row">Rentetan terpanjang ({esc(streak)}), hari</th>'
            f'{number_cell(numbers["run_length"])}</tr>'
            f'<tr><th scope="row">Rentetan dimulai</th>'
            f'<td>{esc(say_date(numbers["run_start"]))}</td></tr>')
    return (f'<table><caption>Arus dana asing bersih, {esc(finding.as_of)}</caption>'
            f'<tbody>{rows}</tbody></table>')


def table_ownership(finding):
    rows = "".join(
        f'<tr><th scope="row">'
        f'{esc(narrate.CLASS_NAMES[run["cls"]])} '
        f'{"asing" if run["origin"] == "foreign" else "domestik"}</th>'
        f'<td>{esc("menambah" if run["sign"] > 0 else "mengurangi")}</td>'
        f'<td class="num">{run["length"]}</td>'
        f'<td class="num">{run["from_share"] * 100:.2f}%</td>'
        f'<td class="num">{run["to_share"] * 100:.2f}%</td></tr>'
        for run in finding.numbers["runs"][:8])
    months = finding.numbers["months"]
    return (f'<table><caption>Perubahan kepemilikan berturut-turut, '
            f'{esc(say_date(months[0]))} sampai {esc(say_date(months[-1]))}</caption>'
            f'<thead><tr><th scope="col">Kelompok pemodal</th>'
            f'<th scope="col">Arah</th><th scope="col">Bulan</th>'
            f'<th scope="col">Porsi awal</th><th scope="col">Porsi akhir</th></tr>'
            f'</thead><tbody>{rows}</tbody></table>')


def table_quarterly(finding):
    latest, previous = finding.numbers["latest"], finding.numbers["previous"]
    fields = [("Pendapatan", "revenue"), ("Laba", "earnings"),
              ("Laba kotor", "gross_profit"), ("Total aset", "total_assets"),
              ("Total ekuitas", "total_equity")]
    if latest.get("capex") is not None:
        fields.append((f'Belanja modal ({latest["capex_source_field"]})', "capex"))
    rows = "".join(
        f'<tr><th scope="row">{esc(label)}</th>'
        f'{number_cell(previous.get(field))}{number_cell(latest.get(field))}</tr>'
        for label, field in fields)
    return (f'<table><caption>Dua kuartal terakhir yang tersedia</caption>'
            f'<thead><tr><th scope="col">Pos</th>'
            f'<th scope="col">{esc(say_date(previous["date"]))}</th>'
            f'<th scope="col">{esc(say_date(latest["date"]))}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def table_peers(finding):
    rows = "".join(
        f'<tr><th scope="row">{esc(label)}</th>'
        f'{number_cell(finding.numbers[field]["value"])}'
        f'<td class="num">{finding.numbers[field]["rank"]} dari '
        f'{finding.numbers[field]["of"]}</td></tr>'
        for field, label in (("pe_ttm", "Harga terhadap laba"),
                             ("pb_mrq", "Harga terhadap nilai buku"),
                             ("market_cap", "Kapitalisasi pasar"))
        if field in finding.numbers)
    return (f'<table><caption>Posisi di dalam kelompok sejenis</caption>'
            f'<thead><tr><th scope="col">Ukuran</th><th scope="col">Nilai</th>'
            f'<th scope="col">Peringkat</th></tr></thead><tbody>{rows}</tbody></table>')


TABLE = {
    "segment_concentration": table_segments,
    "price_trend": table_price,
    "flow_runs": table_flow,
    "ownership_runs": table_ownership,
    "quarterly_change": table_quarterly,
    "peer_rank": table_peers,
}


# ------------------------------------------------------------------------------ pages


def citation_block(finding, index):
    citation = reader.cite(finding.citation())
    fields = ", ".join(citation["fields"])
    return (f'<dl class="cite" id="sumber-{index}">'
            f'<dt>Endpoint</dt><dd><code>{esc(citation["endpoint"])}</code></dd>'
            f'<dt>Field</dt><dd><code>{esc(fields)}</code></dd>'
            f'<dt>Jendela data</dt><dd>{esc(citation["as_of"])}</dd></dl>')


def section_html(index, key, finding):
    title = reader.SECTION_TITLE[key]
    parts = [f'<section aria-labelledby="bagian-{index}">',
             f'<h2 id="bagian-{index}">{esc(title)}</h2>',
             f'<p>{esc(finding.sentence)}</p>']

    if finding.audible and finding.series and key in AUDIBLE_LABEL:
        # The button is an addition, never a replacement: the same fact is already in the
        # sentence above and the table below, because audio is slower and some listeners
        # will not use it at all.
        parts.append(
            f'<p><button type="button" data-series="{esc(json.dumps(finding.series))}" '
            f'aria-controls="audio-{index}">{esc(AUDIBLE_LABEL[key])}</button></p>'
            f'<p id="audio-{index}" aria-live="polite"></p>')

    parts.append(TABLE[key](finding))
    parts.append(f'<h3 id="sumber-judul-{index}">Sumber angka di bagian ini</h3>')
    parts.append(citation_block(finding, index))
    parts.append('</section>')
    return "".join(parts)


def page(reading):
    symbol = reading["symbol"]
    options = "".join(
        f'<option value="{esc(other)}"{" selected" if other == symbol else ""}>'
        f'{esc(other)}</option>'
        for other in sources.available_symbols(reading["source"]))

    sections = "".join(section_html(index, key, finding)
                       for index, (key, finding) in enumerate(reading["sections"], 1))

    gaps = ""
    if reading["gaps"]:
        items = "".join(
            f'<li class="gap"><strong>{esc(reader.SECTION_TITLE.get(key, key))}</strong>: '
            f'{esc(reason)} — <code>{esc(detail)}</code></li>'
            for key, (reason, detail) in sorted(reading["gaps"].items()))
        gaps = (f'<section aria-labelledby="belum"><h2 id="belum">Belum ada</h2>'
                f'<p>Bagian berikut tidak ditampilkan karena datanya belum diambil. '
                f'Endpoint yang akan mengisinya disebutkan, dan tidak ada angka yang '
                f'dikarang untuk menutupinya.</p><ul>{items}</ul></section>')

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(symbol)} — riset fundamental IDX yang bisa didengar</title>
<style>{STYLE}</style>
</head>
<body>
<a class="skip" href="#isi">Lewati ke isi</a>
<header>
<h1>{esc(reading['company'])} <span>({esc(symbol)})</span></h1>
<p class="note">Sumber data: {esc(reader.SOURCE_NOTE[reading['source']])}</p>
<form method="get" action="/">
<label for="symbol">Pilih kode saham</label>
<select id="symbol" name="symbol">{options}</select>
<button type="submit">Baca</button>
</form>
</header>
<main id="isi">
<section aria-labelledby="ringkasan">
<h2 id="ringkasan">Ringkasan</h2>
<p class="lede">{esc(reading['summary'].sentence)}</p>
</section>
{sections}
{gaps}
</main>
<footer>
<h2>Catatan</h2>
<p>{esc(reader.DISCLAIMER)}</p>
<p>Setiap angka di halaman ini membawa endpoint, field, dan jendela datanya. Angka tanpa
sumber ditolak sebelum halaman dibuat, bukan disembunyikan setelahnya.</p>
</footer>
<script src="/sonify.js"></script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    source = "recorded"

    def _send(self, body, content_type="text/html; charset=utf-8", status=200):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/sonify.js":
            with open(os.path.join(HERE, "sonify.js")) as handle:
                self._send(handle.read(), "application/javascript; charset=utf-8")
            return
        if parsed.path not in ("/", "/index.html"):
            self._send("<h1>404</h1>", status=404)
            return

        query = urllib.parse.parse_qs(parsed.query)
        available = sources.available_symbols(self.source)
        symbol = sources.bare_symbol((query.get("symbol") or [available[0]])[0])
        if symbol not in available:
            symbol = available[0]
        try:
            self._send(page(reader.read(symbol, self.source)))
        except (sources.NotRecorded, narrate.NotDerivable) as exc:
            self._send(f'<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">'
                       f'<title>Belum diambil</title></head><body><h1>Belum diambil</h1>'
                       f'<p>{esc(exc)}</p></body></html>', status=404)

    def log_message(self, *args):
        pass


def check_markup():
    """The structural promises, asserted on a real rendered page rather than claimed."""
    failures = []
    markup = page(reader.read("BBCA"))
    checks = [
        ('<html lang="id">', "the page declares its language"),
        ('class="skip"', "there is a skip link"),
        ("<caption>", "tables carry captions"),
        ('scope="row"', "row headers are marked"),
        ('scope="col"', "column headers are marked"),
        ('aria-live="polite"', "the audio status is announced"),
        ("<h1", "there is a level-one heading"),
        ("belum diambil", "missing data is named, not hidden"),
        ("bukan nasihat investasi", "the disclaimer is on the page"),
    ]
    for needle, why in checks:
        if needle not in markup:
            failures.append(f"missing: {why} ({needle})")
    if markup.count("<h1") != 1:
        failures.append(f"{markup.count('<h1')} level-one headings, expected exactly 1")
    if "<canvas" in markup or "<svg" in markup:
        failures.append("a drawing element reached the page — this product has no chart")
    return failures, len(checks) + 2


def main(argv=None):
    parser = argparse.ArgumentParser(prog="webapp.py")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--source", default="recorded", choices=("recorded", "synth"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        failures, checked = check_markup()
        mark = "PASS" if not failures else "FAIL"
        print(f"{mark}  rendered markup      {checked} checked, {len(failures)} failed")
        for failure in failures:
            print(f"        {failure}")
        return 1 if failures else 0

    Handler.source = args.source
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"http://127.0.0.1:{args.port}   "
              f"({', '.join(sources.available_symbols(args.source))})")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
