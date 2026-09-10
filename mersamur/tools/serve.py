#!/usr/bin/env python3
"""Papan pipeline di localhost, dirender ulang tiap permintaan.

    python3 tools/serve.py                 # http://127.0.0.1:8080
    python3 tools/serve.py --port 9000 --open
    python3 tools/serve.py --no-evaluate   # lewati gerbang tugas 11, lebih cepat

Nol kredit dan nol pustaka luar: `http.server` dari pustaka standar, dan seluruh
isinya dibaca dari `state/` serta `research/harness/recorded/`. Tidak ada soket
yang dibuka ke Sectors API oleh berkas ini, langsung maupun tidak.

## Kenapa disajikan, bukan cukup berkas statis

`tools/dashboard.py` menulis satu HTML dan itu tetap bentuk yang dikomit. Yang
tidak bisa dilakukan berkas statis adalah **ikut berubah saat berkasnya
berubah**: jalankan `app/tick.py`, `app/backtest.py`, atau geser satu ambang
lewat `app/agent/evolve.py`, dan papan yang tersaji langsung menunjukkan
keadaan barunya tanpa dibangun ulang. Halaman menanyakan `/api/fingerprint`
tiap tiga detik — sidik jari dari mtime dan ukuran berkas keadaan — dan memuat
ulang saat sidik jarinya berbeda.

## Terikat ke loopback dengan sengaja

Bawaannya `127.0.0.1`, bukan `0.0.0.0`. Papan ini memuat seluruh isi paragraf
untuk ticker IDX yang masih diperdagangkan, dan `riset/red-team.md` §D11 menyebut
persis itu sebagai persoalan hukum kalau tersiar tanpa konteksnya. Menyajikannya
ke jaringan adalah keputusan yang harus diambil sadar, jadi ia menuntut
`--host` yang ditulis sendiri dan mencetak peringatan saat dipakai.

## Rute

    GET /                    papan pengguna — catatan per kode saham
    GET /pipeline            catatan pembangunan — tahap, gerbang, backtest
    GET /api/state.json      angka yang sama, sebagai JSON
    GET /api/fingerprint     sidik jari berkas keadaan, untuk muat ulang otomatis
"""
import argparse
import hashlib
import importlib
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config                                  # noqa: E402
from app.render import paragraph as para                # noqa: E402
from tools import dashboard                             # noqa: E402

# Berkas yang membuat papan berubah. Sidik jarinya cuma mtime dan ukuran — cukup
# untuk memicu muat ulang, dan tidak pernah membaca isi berkas besar hanya untuk
# tahu apakah ia berubah.
WATCHED = [
    os.path.join(config.STATE_DIR, "thresholds.json"),
    os.path.join(config.STATE_DIR, "warnings.jsonl"),
    os.path.join(config.STATE_DIR, "outcomes.jsonl"),
    os.path.join(config.STATE_DIR, "lessons.jsonl"),
    os.path.join(config.STATE_DIR, "runs.jsonl"),
    os.path.join(config.STATE_DIR, "credits.jsonl"),
    os.path.join(config.STATE_DIR, "backtest_report.json"),
    os.path.join(config.RECORDED_DIR, "_ledger.jsonl"),
    os.path.join(config.RECORDED_DIR, "_manifest.json"),
    dashboard.__file__,
]


_module_mtime = [os.path.getmtime(dashboard.__file__)]


def refresh_module():
    """Muat ulang perakit papannya sendiri kalau berkasnya berubah.

    Tanpa ini, menyunting `tools/dashboard.py` tidak terlihat sampai server
    dimatikan dan dinyalakan lagi — modulnya sudah diimpor sekali dan Python
    tidak membacanya ulang. Menyunting papan lalu memuat ulang halaman adalah
    lingkar kerja yang paling sering dipakai, jadi ia dibuat bekerja.
    """
    try:
        mtime = os.path.getmtime(dashboard.__file__)
    except OSError:
        return
    if mtime != _module_mtime[0]:
        _module_mtime[0] = mtime
        importlib.reload(dashboard)


def fingerprint():
    digest = hashlib.sha256()
    for path in WATCHED:
        try:
            stat = os.stat(path)
            digest.update(f"{path}:{stat.st_mtime_ns}:{stat.st_size};".encode())
        except FileNotFoundError:
            digest.update(f"{path}:-;".encode())
    return digest.hexdigest()[:16]


PORT_TRIES = 20


def bind(host, port):
    """Porta yang diminta, atau yang berikutnya yang bebas.

    Sebuah papan yang menolak jalan karena porta bawaannya dipakai proses lain
    adalah gangguan tanpa guna: tidak ada yang bergantung pada nomor porta ini.
    Yang dipakai selalu dicetak, jadi tidak ada tebak-tebakan alamat.
    """
    for candidate in range(port, port + PORT_TRIES):
        try:
            return ThreadingHTTPServer((host, candidate), Handler), candidate
        except OSError as exc:
            import errno
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
    return None, None


def jsonable(data):
    """Angka papan sebagai JSON. Objek profil dan paragraf diubah ke dict."""
    rows = []
    for row in data["rows"]:
        if "profile" not in row:
            rows.append({"symbol": row["symbol"], "error": row["error"]})
            continue
        rows.append(row["profile"].to_dict())
    paragraphs = [p if isinstance(p, dict) else p.to_dict()
                  for p in data["paragraphs"]]
    return {
        "profil": rows,
        "paragraf": paragraphs,
        "state": {k: v for k, v in data["state"].items()},
        "ledger": data["ledger"],
        "tes": data["tests"],
        "tugas": data["tasks"],
        "rekaman": data["recordings"],
        "manifes": data["manifest"],
        "gerbang": data["evaluate"],
        "backtest": data["backtest"],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "mersamur"
    sys_version = ""
    with_evaluate = True
    lock = threading.Lock()

    def log_message(self, fmt, *args):          # satu baris, tanpa alamat klien
        sys.stderr.write(f"  {fmt % args}\n")

    def _send(self, body, content_type="text/html; charset=utf-8", status=200):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        # Papan ini tidak memuat apa pun dari luar dan tidak boleh dibingkai.
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "script-src 'unsafe-inline'; connect-src 'self'; "
                         "frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        route = self.path.split("?")[0].rstrip("/") or "/"
        if route == "/api/fingerprint":
            return self._send(fingerprint(), "text/plain; charset=utf-8")
        if route == "/api/state.json":
            with self.lock:
                refresh_module()
                data = dashboard.gather(with_evaluate=self.with_evaluate)
            return self._send(
                json.dumps(jsonable(data), ensure_ascii=False, indent=1,
                           default=str),
                "application/json; charset=utf-8")
        if route in ("/", "/pipeline"):
            mode = "pipeline" if route == "/pipeline" else "user"
            with self.lock:
                refresh_module()
                data = dashboard.gather(
                    with_evaluate=self.with_evaluate and mode == "pipeline")
            try:
                page = dashboard.build(data, live=True, mode=mode)
            except para.BannedVocabularyError as exc:
                # Fail-closed juga saat disajikan: halaman yang gagal periksa
                # tidak dikirim separuh, ia diganti pesan yang menamai sebabnya.
                return self._send(
                    f"<!doctype html><meta charset=utf-8><title>papan tidak "
                    f"dikirim</title><body style='font:15px/1.6 system-ui;"
                    f"max-width:60ch;margin:60px auto;padding:0 20px'>"
                    f"<h1 style='font-size:19px'>Papan tidak dikirim</h1>"
                    f"<p>{exc}</p><p style='color:#666'>Aturan yang sama yang "
                    f"menjaga paragraf produk berlaku untuk papan ini. "
                    f"Perbaiki teksnya di <code>tools/dashboard.py</code>, "
                    f"halaman akan memuat ulang sendiri.</p></body>",
                    status=500)
            return self._send(page)
        return self._send("<!doctype html><meta charset=utf-8>"
                          "<p style='font:15px system-ui;padding:40px'>"
                          "Tidak ada di sini. Papannya di <a href='/'>/</a>, "
                          "catatan pembangunannya di "
                          "<a href='/pipeline'>/pipeline</a>.</p>",
                          status=404)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Sajikan papan pipeline mersamur di localhost. Nol kredit.",
        epilog="Deskriptif, bukan anjuran investasi. Teks lengkapnya: "
               "mersamur/DISCLAIMER.md.")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1",
                    help="bawaan loopback; ubah hanya kalau memang mau "
                         "menyajikannya ke jaringan")
    ap.add_argument("--open", action="store_true",
                    help="buka papannya di browser setelah server siap")
    ap.add_argument("--no-evaluate", action="store_true",
                    help="lewati gerbang tugas 11 saat merakit papan")
    args = ap.parse_args(argv)

    Handler.with_evaluate = not args.no_evaluate
    server, port = bind(args.host, args.port)
    if server is None:
        print(f"tidak ada porta bebas di {args.port}..{args.port + PORT_TRIES - 1} "
              f"pada {args.host}.", file=sys.stderr)
        return 1
    if port != args.port:
        print(f"porta {args.port} sedang dipakai proses lain — memakai {port}.")
    url = f"http://{args.host}:{port}/"

    print(f"papan mersamur  {url}")
    print(f"  state         {config.STATE_DIR}")
    print(f"  rekaman       {config.RECORDED_DIR}")
    print(f"  sidik jari    {fingerprint()}  (halaman memuat ulang saat berubah)")
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"  catatan: terikat ke {args.host}, jadi papan ini terjangkau dari "
              f"jaringan. Isinya memuat ticker yang masih diperdagangkan.")
    print("  Ctrl-C untuk berhenti")

    if args.open:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
