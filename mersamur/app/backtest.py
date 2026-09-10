#!/usr/bin/env python3
"""Tugas 12 — walk-forward atas 20 bulan riwayat berlabel, dengan hold-out bersih.

`riset/red-team.md` §A3 memuat kontradiksi yang tugas ini selesaikan. `spec.md` §6
mensyaratkan N >= 20 peringatan selesai per sumbu sebelum sebuah ambang boleh
bergeser. Dengan base rate 0,77% per saham per 10 hari bursa
(`riset/temuan-kelayakan.md` §Q4), forward test 14 hari hanya menghasilkan 3-5 true
positive. Ambang tidak akan pernah menyala pada data live, dan melanggar pagarnya
demi satu adegan video berarti mempertunjukkan overfitting di depan juri.

Pemisahannya dua rezim, dan modul ini adalah rezim pertama:

    Penyetelan   replay historis walk-forward   di sini ambang boleh bergerak
    Forward test run harian sejak sekarang      validasi saja, tidak pernah menyetel

**Apa yang membuat replay ini jujur, dan bukan kurva yang mencurigakan.**

*Satu pintu ke masa lalu.* Setiap fitur pada tanggal T dibaca lewat `AsOfCache(T)`,
pembungkus rekaman yang memotong tiap payload bertanggal ke baris **sebelum** T dan
menahan payload yang tidak bisa dipotong. Modul sumbu tidak diubah sama sekali: ia
menerima cache seperti biasa dan tidak punya cara melihat melewatinya. Itulah yang
membuat sifat "fitur pada T tidak berubah kalau data setelah T dihapus" bisa diuji
dengan membandingkan dua korpus, bukan dengan mempercayai komentar.

*Gagal tertutup.* Payload yang tidak dikenali aturan pemotongannya ditahan, bukan
diloloskan. Panel broker adalah kasus utamanya: `/v2/broker-summary/{symbol}/top/`
mengembalikan satu agregat atas jendela 2026-06-11..2026-09-09 tanpa rincian
harian, jadi ia tidak bisa dipotong pada T mana pun di dalam periode uji. Ia ditahan,
sumbu konsentrasi berbunyi `tidak_diketahui`, dan laporan menyebut berapa kali itu
terjadi. Menganggapnya "tidak menyala" akan membuat saham yang datanya tidak dibeli
terlihat tenang.

*Satu jalur penilaian.* Confusion matrix tetap hanya dibangun di `evaluate.score()`,
dan setiap pesaing tetap dirakit oleh `evaluate.contenders()` — sama persis dengan
tugas 11. Modul ini menambahkan sumbu waktu di luarnya, lalu **menjumlahkan** matriks
per tanggal. Tidak ada rumus lift kedua di berkas ini.

*Hold-out tidak pernah dilihat untuk memilih apa pun.* Tugas ini tidak menyetel
apa-apa: ambang dibaca dari `state/thresholds.json` seperti adanya dan evolve step
milik tugas 17. Jadi hold-out di sini masih perawan, dan laporan mencatatnya sebagai
fakta yang bisa dibantah (`holdout_dipakai_menyetel: false`), bukan sebagai janji.

**Yang akan dibaca laporan ini, dan sebabnya.** Rekaman yang sudah dibayar memuat
`/v2/daily/` hanya untuk 2026-08-10..2026-09-09 dan `/v2/news/` hanya untuk
2026-08-27..2026-09-08. Di seluruh set penyetelan (T < hold-out) tidak ada satu pun
sesi harga yang terlihat, jadi tiga dari empat sumbu tidak terukur dan sistem empat
sumbu tidak bisa mengeluarkan peringatan di sana. Itu temuan negatif tentang
**cakupan data**, bukan tentang model, dan §6 tugas ini meminta temuan seperti itu
ditulis apa adanya. `render()` menyatakannya di muka supaya angka nol tidak terbaca
sebagai model yang kalah.

Nol kredit: seluruhnya membaca `research/harness/recorded/`. `SectorsClient` tidak
diimpor di sini maupun di apa pun yang dipanggil dari sini.
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta

# Dijalankan sebagai skrip (`python3 app/backtest.py`), bentuk yang dipakai
# "Kriteria selesai", jadi akar paket harus ada di path sebelum impor pertama.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import baselines, config, evaluate, labels, universe  # noqa: E402
from app.axes import catalyst, concentration, volume_anomaly  # noqa: E402
from app.cache import Cache, Hit  # noqa: E402

# --- parameter, semuanya di satu tempat -------------------------------------
# Label hanya ada sejak 2025 (`app.labels.REGIME_START`): nol suspensi cooling-down
# sebelum itu. Tugas ini §2 melarang menyentuh yang lebih tua.
DEFAULT_START = labels.REGIME_START

# Batas hold-out bawaan, sama dengan yang disebut "Kriteria selesai".
DEFAULT_HOLDOUT = date(2026, 7, 1)

# Jendela hasil: peristiwa dalam 10 hari bursa sesudah T (§1).
HORIZON_SESSIONS = 10

# Langkah grid dalam hari bursa. Mingguan, bukan harian: 20 bulan harian adalah
# ~420 tanggal x 200 emiten dan perintah di "Kriteria selesai" harus selesai dalam
# hitungan menit. Angkanya parameter (`--step`), bukan konstanta tersembunyi, dan
# ia tercatat di laporan supaya sebuah angka bisa direproduksi.
DEFAULT_STEP = 5

REPORT_PATH = os.path.join(config.STATE_DIR, "backtest_report.json")

SPLIT_TUNING = "penyetelan"
SPLIT_HOLDOUT = "hold_out"


# --- kalender ---------------------------------------------------------------
def trading_days_forward(start, count):
    """`count` hari bursa **sesudah** `start`, terlama dulu.

    Cerminan `volume_anomaly.trading_days_back`, dan seperti fungsi itu ia menyerahkan
    kalendernya ke `config.is_trading_day`. Perhatikan batas kalender itu: himpunan
    liburnya milik 2026 saja, jadi 2025 dimodelkan sebagai hari kerja belaka. Jendela
    hasil 2025 karenanya sedikit lebih pendek dari 10 sesi sebenarnya — tidak lengkap,
    bukan keliru dengan percaya diri, dan disebut di laporan.
    """
    out, day, guard = [], start + timedelta(days=1), 0
    while len(out) < count and guard < count * 4 + 30:
        if config.is_trading_day(day):
            out.append(day)
        day += timedelta(days=1)
        guard += 1
    return out


def horizon(when, sessions=HORIZON_SESSIONS):
    """`(hari_pertama, hari_terakhir)` dari jendela hasil sesudah `when`, atau None.

    Terbuka di T: sebuah peristiwa yang **bertanggal** T bukan hasil, ia sudah
    terjadi pada saat keputusan diambil.
    """
    days = trading_days_forward(when, sessions)
    return (days[0], days[-1]) if days else None


def grid(start, end, step=DEFAULT_STEP):
    """Hari bursa dari `start` sampai `end` inklusif, tiap `step` sesi."""
    out, day, step = [], start, max(int(step), 1)
    seen = 0
    while day <= end:
        if config.is_trading_day(day):
            if seen % step == 0:
                out.append(day)
            seen += 1
        day += timedelta(days=1)
    return out


# --- pintu tunggal ke masa lalu ---------------------------------------------
class AsOfCache:
    """Rekaman sebagaimana ia berdiri **sebelum** `as_of`. Menahan yang ragu.

    Komposisi, bukan turunan `Cache`: mewarisi `_payload` akan memberi jalan kedua ke
    berkas mentah, dan satu-satunya nilai modul ini adalah tidak adanya jalan kedua.

    Empat aturan pemotongan, satu per endpoint bertanggal, plus daftar putih
    referensi tak bertanggal. Apa pun di luar itu ditahan dan dicatat di
    `withheld_paths` — sebuah payload yang tidak diketahui tanggalnya tidak boleh
    lolos hanya karena tidak ada yang menuliskan aturannya.
    """

    # Referensi tak bertanggal: daftar broker dan baris screener. Keduanya tetap
    # snapshot September 2026, jadi keanggotaan universe adalah kebocoran seleksi
    # yang diketahui — dinyatakan di laporan, bukan disembunyikan di sini.
    UNDATED_REFERENCE = (universe.SCREENER_PATH, concentration.BROKERS_PATH)

    def __init__(self, as_of, source=None):
        self.as_of = as_of if isinstance(as_of, date) else labels.parse_date(as_of)
        if self.as_of is None:
            raise ValueError(
                "AsOfCache butuh tanggal (date atau 'YYYY-MM-DD'); tanpa itu tidak "
                "ada batas kebocoran.")
        self._source = source if source is not None else Cache()
        self._memo = {}
        self.withheld_paths = set()

    # --- permukaan yang sama seperti Cache ---------------------------------
    @property
    def root(self):
        return self._source.root

    def manifest(self, reload=False):
        """Indeksnya diteruskan apa adanya: ia mencatat panggilan mana yang pernah
        dibayar, bukan isi bertanggal, dan `series()` membacanya untuk memilih bentuk
        parameter. Menyaringnya akan menyembunyikan panggilan, bukan masa depan."""
        return self._source.manifest(reload=reload)

    def entry(self, path, params=None, method="GET"):
        return self._source.entry(path, params, method)

    def __len__(self):
        return len(self._source)

    def __repr__(self):
        return f"<AsOfCache {self.as_of.isoformat()} atas {self._source!r}>"

    # --- pemotongan ---------------------------------------------------------
    def get(self, path, params=None, method="GET"):
        """`Hit` yang isinya sudah dipotong ke sebelum `as_of`, atau None.

        None berarti dua hal yang sengaja tidak dibedakan di sini: panggilan itu tidak
        pernah dibeli, atau isinya tidak bisa dipotong dengan aman. Keduanya berujung
        sama di sumbu — `tidak_diketahui` — dan yang kedua dihitung di
        `withheld_paths` supaya laporan bisa menyebutnya.
        """
        key = (path, tuple(sorted((params or {}).items())), method)
        if key in self._memo:
            return self._memo[key]
        self._memo[key] = hit = self._truncate(path, self._source.get(
            path, params, method))
        return hit

    def _truncate(self, path, hit):
        if hit is None:
            return None
        if not hit.found:
            # 404 yang sudah dibayar tetap 404 pada tanggal mana pun: pencarian itu
            # dijalankan dan tidak mengandung apa pun yang bertanggal.
            return hit

        if path.startswith("/v2/daily/"):
            return self._filter_rows(hit, "date")
        if path == catalyst.NEWS_PATH:
            return self._filter_rows(hit, "timestamp")
        if path == labels.SUSPENSIONS_PATH:
            return self._filter_rows(hit, "suspension_date")
        if path.startswith("/v2/broker-summary/"):
            return self._window_guard(hit, path)
        if path in self.UNDATED_REFERENCE:
            return hit

        self.withheld_paths.add(path)
        return None

    def _filter_rows(self, hit, field):
        """Baris dengan `field` pada atau sesudah `as_of` dibuang.

        Amplopnya dipertahankan: `{"results": [...]}` tetap dict dengan `results`
        kosong, bukan None. Deret kosong berarti "belum ada sesi tercatat", yang di
        sumbu terbaca `tidak_diketahui` — berbeda dari deret nol seluruhnya, yang
        berarti sahamnya dihentikan.
        """
        payload = hit.payload
        rows = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            # Amplop tak dikenal. Tidak ada yang bisa dipotong, jadi ditahan.
            self.withheld_paths.add(hit.meta.get("path") or "")
            return None
        kept = [r for r in rows
                if isinstance(r, dict) and self._before(r.get(field))]
        if isinstance(payload, dict):
            trimmed = dict(payload)
            trimmed["results"] = kept
        else:
            trimmed = kept
        return Hit(hit.key, hit.status, trimmed, hit.meta)

    def _window_guard(self, hit, path):
        """Agregat jendela: lolos hanya kalau seluruh jendelanya berakhir sebelum T.

        Panel broker tidak punya rincian harian, jadi tidak ada yang bisa dipotong.
        Satu-satunya pilihan jujur adalah semua atau tidak sama sekali.
        """
        payload = hit.payload if isinstance(hit.payload, dict) else {}
        end = labels.parse_date(payload.get("end"))
        if end is not None and end < self.as_of:
            return hit
        self.withheld_paths.add(path)
        return None

    def _before(self, value):
        when = labels.parse_date(value)
        return when is not None and when < self.as_of


# --- hasil ------------------------------------------------------------------
def outcomes(symbols, when, sessions=HORIZON_SESSIONS, cache=None):
    """Emiten yang kena suspensi cooling-down di dalam jendela hasil sesudah `when`.

    Dibaca dari `Cache` penuh dan **bukan** dari `AsOfCache`: ini label, bukan fitur.
    Memakai cache terpotong di sini akan membuat setiap hasil tidak terlihat dan
    seluruh backtest melaporkan nol peristiwa.

    `labels` tetap satu-satunya pintu ke kelas positif, jadi aturan §Q4 — hanya
    `cooling_down`, hanya sejak 2025 — tidak ditulis ulang di sini.
    """
    span = horizon(when, sessions)
    if span is None:
        return frozenset()
    first, last = span
    wanted = frozenset(universe.normalize(s) for s in symbols)
    return frozenset(
        e.symbol for e in labels.events(after=first, before=last + timedelta(days=1),
                                        cache=cache)
        if e.is_label and e.symbol in wanted)


def censoring_limit(cache=None, sessions=HORIZON_SESSIONS):
    """Tanggal T terakhir yang jendela hasilnya masih seluruhnya ada di arsip.

    Sesudah tanggal ini hasilnya belum bisa diamati — sebuah nol di sana berarti
    "arsipnya habis", bukan "tidak terjadi apa-apa". Tanggal seperti itu dibuang dari
    grid dan jumlahnya dilaporkan.
    """
    archive = labels.load_events(cache=cache)
    if not archive:
        return None
    last = archive[-1].date
    day = last
    while day > labels.REGIME_START:
        span = horizon(day, sessions)
        if span is not None and span[1] <= last:
            return day
        day -= timedelta(days=1)
    return None


# --- akumulasi ---------------------------------------------------------------
def pool(system, results):
    """Confusion matrix gabungan dari banyak tanggal, sebagai `evaluate.Result`.

    Penjumlahan, bukan rumus baru. `precision`, `recall` dan `lift` tetap properti
    `evaluate.Result` yang sama persis dengan yang dipakai tugas 11, jadi tidak ada
    definisi lift kedua di repo ini.
    """
    rows = list(results)
    tp = sum(r.tp for r in rows)
    fn = sum(r.fn for r in rows)
    n = sum(r.n for r in rows)
    return evaluate.Result(
        system=system, n=n,
        warnings=sum(r.warnings for r in rows),
        tp=tp, fp=sum(r.fp for r in rows), fn=fn,
        tn=sum(r.tn for r in rows),
        base_rate=(tp + fn) / n if n else 0.0,
        # Daftar emiten sengaja dikosongkan di tingkat gabungan. Sebuah simbol yang
        # muncul di sini berarti "diperingatkan pada suatu tanggal", dan tanggal itu
        # sudah hilang — 4.900 baris tanpa tanggal terbaca seperti 4.900 emiten.
        # Daftar yang masih punya tanggalnya ada di `per_tanggal` di laporan.
        warned_symbols=(),
        missed_symbols=(),
    )


@dataclass(frozen=True)
class DateResult:
    """Satu tanggal T: pesaing, matriks per pesaing, dan berapa peristiwa terjadi."""

    when: str
    horizon_start: str
    horizon_end: str
    n_symbols: int = 0
    n_events: int = 0
    events: tuple = ()
    results: dict = None
    availability: dict = None
    withheld: tuple = ()


def availability(symbols, source, cache=None):
    """Berapa banyak data yang benar-benar terlihat pada T, per endpoint.

    Bukan pengukuran sumbu — pengukuran **bahan bakunya**. Ini yang menjelaskan
    kenapa sebuah sumbu berbunyi `tidak_diketahui`, dan ia dihitung langsung dari
    `AsOfCache` sehingga tidak perlu membangun profil untuk kedua kalinya.
    """
    with_sessions = with_news = with_panel = 0
    for symbol in symbols:
        want = universe.normalize(symbol)
        try:
            if len(volume_anomaly.series(want, cache=source)) > 0:
                with_sessions += 1
        except (volume_anomaly.NoDailyDataError, ValueError, LookupError):
            pass
        try:
            if catalyst.score(want, cache=source).n_articles > 0:
                with_news += 1
        except (catalyst.NoNewsDataError, ValueError, LookupError):
            pass
        try:
            concentration.panel(want, cache=source)
            with_panel += 1
        except (concentration.NoBrokerDataError, ValueError, LookupError):
            pass
    return {"n": len(symbols), "deret_harian": with_sessions,
            "artikel": with_news, "panel_broker": with_panel}


def run_date(when, symbols, cache=None, sessions=HORIZON_SESSIONS,
             thresholds_path=None):
    """Satu tanggal walk-forward, dari fitur sampai matriks.

    Fitur lewat `AsOfCache(when)`; hasil lewat `Cache` penuh. Perakitan pesaing dan
    penilaiannya diserahkan bulat-bulat ke `app.evaluate`.
    """
    source = AsOfCache(when, source=cache)
    truth = outcomes(symbols, when, sessions=sessions, cache=cache)
    calls = evaluate.contenders(when, symbols, cache=source,
                                thresholds_path=thresholds_path)
    span = horizon(when, sessions)
    return DateResult(
        when=when.isoformat(),
        horizon_start=span[0].isoformat() if span else "",
        horizon_end=span[1].isoformat() if span else "",
        n_symbols=len(symbols),
        n_events=len(truth),
        events=tuple(sorted(truth)),
        results=evaluate.score_all(calls, truth),
        availability=availability(symbols, source, cache=cache),
        withheld=tuple(sorted(source.withheld_paths)),
    )


def split_of(when, holdout):
    return SPLIT_HOLDOUT if when >= holdout else SPLIT_TUNING


def summarize(rows):
    """`{sistem: Result}` gabungan plus hitungan tanggal, peristiwa dan ketersediaan."""
    rows = list(rows)
    systems = []
    for row in rows:
        for name in row.results:
            if name not in systems:
                systems.append(name)
    keys = ("n", "deret_harian", "artikel", "panel_broker")
    return {
        "n_tanggal": len(rows),
        "n_peristiwa": sum(r.n_events for r in rows),
        "rentang": [rows[0].when, rows[-1].when] if rows else [],
        "results": {name: pool(name, [r.results[name] for r in rows
                                      if name in r.results]).to_dict()
                    for name in systems},
        "ketersediaan": {k: sum(r.availability.get(k, 0) for r in rows)
                         for k in keys},
    }


# --- laporan -----------------------------------------------------------------
def findings(splits, regimes, parameters):
    """Kalimat-kalimat yang harus ada di laporan, termasuk yang tidak menguntungkan.

    §6: kalau hold-out tidak lebih baik dari baseline, itu ditulis. Fungsi ini
    menuliskannya tanpa syarat — tidak ada cabang yang diam ketika hasilnya buruk.
    """
    out = []
    holdout = splits.get(SPLIT_HOLDOUT, {})
    tuning = splits.get(SPLIT_TUNING, {})

    for name, split in ((SPLIT_TUNING, tuning), (SPLIT_HOLDOUT, holdout)):
        results = split.get("results") or {}
        system = results.get(evaluate.SYSTEM) or {}
        rivals = {n: results.get(n, {}) for n in baselines.NAMES}
        if not system:
            continue
        if system.get("lift") is None:
            out.append(
                f"{name}: sistem {evaluate.SYSTEM} mengeluarkan "
                f"{system.get('warnings', 0)} peringatan, jadi liftnya tidak "
                f"terdefinisi. Itu bukan kekalahan yang terukur — tidak ada angka "
                f"untuk dibandingkan dengan baseline mana pun.")
        else:
            for rival, row in rivals.items():
                if row.get("lift") is None:
                    out.append(f"{name}: {rival} tidak mengeluarkan peringatan, "
                               f"liftnya tidak terdefinisi, jadi tidak dibandingkan.")
                elif system["lift"] > row["lift"]:
                    out.append(f"{name}: {evaluate.SYSTEM} lift "
                               f"{system['lift']:.2f} > {rival} {row['lift']:.2f}.")
                else:
                    out.append(f"{name}: {evaluate.SYSTEM} lift "
                               f"{system['lift']:.2f} TIDAK melampaui {rival} "
                               f"{row['lift']:.2f}.")

    tersedia = (tuning.get("ketersediaan") or {})
    if tersedia.get("n") and not tersedia.get("deret_harian"):
        out.append(
            "Set penyetelan tidak punya satu pun sesi harga yang terlihat: rekaman "
            "hanya memuat /v2/daily/ untuk 2026-08-10..2026-09-09, seluruhnya di sisi "
            "hold-out. Tiga dari empat sumbu karenanya tidak terukur di sana, dan "
            "angka nol pada baris sistem adalah pernyataan tentang cakupan data, "
            "bukan tentang model.")
    if not (splits.get(SPLIT_HOLDOUT, {}).get("n_peristiwa")):
        out.append("Hold-out tidak memuat satu peristiwa berlabel pun di universe "
                   "ini, jadi liftnya tidak bisa diperkirakan sama sekali.")
    elif splits[SPLIT_HOLDOUT]["n_peristiwa"] < 20:
        out.append(
            f"Hold-out hanya memuat {splits[SPLIT_HOLDOUT]['n_peristiwa']} "
            f"pasangan (tanggal, emiten) berlabel. Angka apa pun dari sana punya "
            f"selang kepercayaan yang lebar dan tidak boleh dikutip sebagai "
            f"presisi produk.")

    for year, row in sorted(regimes.items()):
        out.append(f"Rezim {year}: {row['n_peristiwa']} pasangan berlabel atas "
                   f"{row['n_tanggal']} tanggal. Base rate tiap rezim berbeda, jadi "
                   f"angka lintas tahun tidak boleh digabung begitu saja.")

    out.append(
        f"Hold-out tidak dipakai untuk memilih apa pun pada jalankan ini: ambang "
        f"dibaca apa adanya dari state/thresholds.json versi "
        f"{parameters.get('thresholds_version')} dan tidak ada parameter yang "
        f"digeser. Sekali ia dilihat untuk menyetel, ia bukan hold-out lagi.")
    return tuple(out)


def report(start=None, end=None, holdout=None, step=DEFAULT_STEP, size=None,
           symbols=None, cache=None, sessions=HORIZON_SESSIONS,
           thresholds_path=None):
    """Seluruh isi `state/backtest_report.json` sebagai satu dict."""
    from app import axes as axes_mod

    holdout = holdout or DEFAULT_HOLDOUT
    start = start or DEFAULT_START
    limit = censoring_limit(cache=cache, sessions=sessions)
    requested_end = end or limit or start
    end = min(requested_end, limit) if limit else requested_end

    names = (list(symbols) if symbols is not None
             else universe.watchlist(size=size or universe.DEFAULT_SIZE,
                                     cache=cache))
    dates = grid(start, end, step=step)

    rows = [run_date(when, names, cache=cache, sessions=sessions,
                     thresholds_path=thresholds_path) for when in dates]

    by_split = {SPLIT_TUNING: [], SPLIT_HOLDOUT: []}
    by_year = {}
    for row in rows:
        when = labels.parse_date(row.when)
        by_split[split_of(when, holdout)].append(row)
        by_year.setdefault(when.year, []).append(row)

    splits = {name: summarize(group) for name, group in by_split.items()}
    regimes = {str(year): summarize(group) for year, group in sorted(by_year.items())}
    withheld = sorted({p for row in rows for p in row.withheld})

    parameters = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "end_diminta": requested_end.isoformat() if hasattr(requested_end, "isoformat")
        else str(requested_end),
        "batas_sensor": limit.isoformat() if limit else None,
        "holdout": holdout.isoformat(),
        "step_hari_bursa": step,
        "horizon_hari_bursa": sessions,
        "min_axes": config.WARNING_AXES_THRESHOLD,
        "top_n_momentum": baselines.momentum.TOP_N,
        "thresholds_version": axes_mod.version(thresholds_path),
        "universe": len(names),
        "holdout_dipakai_menyetel": False,
    }

    return {
        "tugas": 12,
        "kredit": 0,
        "parameters": parameters,
        "grid": {
            "n_tanggal": len(dates),
            "pertama": dates[0].isoformat() if dates else None,
            "terakhir": dates[-1].isoformat() if dates else None,
            "dibuang_karena_sensor": (
                (requested_end - end).days if limit and requested_end > end else 0),
        },
        "universe": list(names),
        "splits": splits,
        "regimes": regimes,
        "per_tanggal": [
            {"tanggal": r.when, "horizon": [r.horizon_start, r.horizon_end],
             "n_emiten": r.n_symbols, "n_peristiwa": r.n_events,
             "peristiwa": list(r.events),
             "ketersediaan": r.availability,
             "results": {n: v.to_dict() for n, v in (r.results or {}).items()}}
            for r in rows],
        "ditahan": withheld,
        "batas": [
            "Baris screener dan daftar broker adalah snapshot September 2026 dan "
            "tidak bertanggal, jadi keanggotaan universe pada T lebih awal memakai "
            "informasi yang belum ada saat itu. Ini kebocoran seleksi yang diketahui "
            "dan tidak bisa diperbaiki tanpa membeli screener historis.",
            "Kalender libur hanya milik 2026 (config.IDX_HOLIDAYS_2026), jadi jendela "
            "hasil 2025 dihitung atas hari kerja belaka dan sedikit lebih pendek dari "
            "10 sesi sebenarnya.",
            "Panel broker adalah agregat satu jendela tanpa rincian harian, jadi ia "
            "tidak bisa dipotong pada T dan sumbu konsentrasi tidak terukur di "
            "seluruh periode uji.",
        ],
        "temuan": list(findings(splits, regimes, parameters)),
    }


# --- penyajian ---------------------------------------------------------------
def _id(value):
    """Format angka cara Indonesia: koma sebagai pemisah desimal."""
    return str(value).replace(".", ",")


def _pct(value):
    return "-" if value is None else _id("%.2f" % (value * 100)) + "%"


def _lift(value):
    """Lift tanpa penyebut dicetak `-`, tidak pernah `0,00x`.

    Aturan yang sama dengan `evaluate._lift`: aturan yang tidak memperingatkan apa
    pun punya lift tak terdefinisi, dan mencetak angka di sana akan terbaca sebagai
    kekalahan yang terukur, bukan pengukuran yang tidak ada.
    """
    return "-" if value is None else _id("%.2f" % value) + "x"


def _table(title, split):
    lines = [f"  {title}",
             f"    tanggal          : {split['n_tanggal']}"
             f"  ·  pasangan berlabel: {split['n_peristiwa']}"]
    tersedia = split.get("ketersediaan") or {}
    if tersedia.get("n"):
        lines.append(
            f"    bahan baku       : {tersedia['deret_harian']}/{tersedia['n']} "
            f"pasangan punya deret harian, {tersedia['artikel']}/{tersedia['n']} "
            f"punya artikel, {tersedia['panel_broker']}/{tersedia['n']} punya panel "
            f"broker")
    lines.append(f"    {'SISTEM':<26}{'PERINGATAN':>11}{'TP':>5}{'FP':>5}{'FN':>5}"
                 f"{'TN':>7}{'BASE':>8}{'LIFT':>8}{'PRESISI':>9}{'RECALL':>8}")
    for name, r in (split.get("results") or {}).items():
        lines.append(
            f"    {name:<26}{r['warnings']:>11}{r['tp']:>5}{r['fp']:>5}{r['fn']:>5}"
            f"{r['tn']:>7}{_pct(r['base_rate']):>8}{_lift(r['lift']):>8}"
            f"{_pct(r['precision']):>9}{_pct(r['recall']):>8}")
    return lines


def render(data):
    """Laporan lengkap sebagai teks. Deskriptif — tidak ada vonis, warna, atau anjuran."""
    p = data["parameters"]
    lines = [
        "Backtest walk-forward — tugas 12 (0 kredit, dari rekaman)",
        f"  periode          : {p['start']} .. {p['end']}"
        + (f" (diminta sampai {p['end_diminta']}, dipotong di batas sensor "
           f"{p['batas_sensor']})" if p["end"] != p["end_diminta"] else ""),
        f"  hold-out mulai   : {p['holdout']}  — tidak dipakai menyetel apa pun "
        f"pada jalankan ini",
        f"  grid             : tiap {p['step_hari_bursa']} hari bursa, "
        f"{data['grid']['n_tanggal']} tanggal",
        f"  jendela hasil    : {p['horizon_hari_bursa']} hari bursa sesudah T, "
        f"terbuka di T",
        f"  universe         : {p['universe']} emiten (screener 200 terkecil)",
        f"  ambang           : {p['min_axes']} dari 4 sumbu, thresholds versi "
        f"{p['thresholds_version']} — dibaca, tidak digeser",
        "",
        "  Fitur pada tiap T dibaca lewat AsOfCache(T): payload bertanggal dipotong ke "
        "baris sebelum T, payload yang tidak bisa dipotong ditahan. Matriksnya tetap "
        "dibangun di evaluate.score() — jalur penilaian yang sama dengan tugas 11.",
        "",
    ]

    lines += _table(f"SET PENYETELAN (T < {p['holdout']}) — di sini ambang boleh "
                    f"bergerak", data["splits"][SPLIT_TUNING])
    lines += [""]
    lines += _table(f"HOLD-OUT (T >= {p['holdout']}) — angka yang boleh dikutip",
                    data["splits"][SPLIT_HOLDOUT])

    lines += ["", "  PER REZIM TAHUN (base rate tiap tahun berbeda):"]
    for year, row in sorted(data["regimes"].items()):
        lines += _table(f"rezim {year}", row)
        lines.append("")

    if data["ditahan"]:
        lines += ["  Payload yang ditahan karena tidak bisa dipotong pada T:"]
        for path in data["ditahan"]:
            lines.append(f"    - {path}")
        lines.append("")

    lines += ["  Batas yang melekat pada angka di atas:"]
    for note in data["batas"]:
        lines.append(f"    - {note}")

    lines += ["", "  TEMUAN:"]
    for note in data["temuan"]:
        lines.append(f"    - {note}")

    lines += [
        "",
        "  Seluruh isi laporan ini deskriptif: catatan atas angka yang dikembalikan "
        "API dan atas apa yang tidak terukur, bukan penilaian atas emiten mana pun "
        "maupun anjuran tindakan.",
    ]
    return "\n".join(lines)


def write_report(data, path=REPORT_PATH):
    """Laporan penuh ke `state/backtest_report.json`, dibuat utuh."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        fh.write("\n")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Replay walk-forward atas riwayat berlabel 2025-2026. 0 kredit.")
    parser.add_argument("--walk-forward", action="store_true",
                        help="jalankan replaynya dan tulis laporan")
    parser.add_argument("--holdout", default=DEFAULT_HOLDOUT.isoformat(),
                        help="tanggal mulai hold-out (bawaan 2026-07-01)")
    parser.add_argument("--start", default=DEFAULT_START.isoformat(),
                        help="awal periode (bawaan 2025-01-01, awal rezim label)")
    parser.add_argument("--end", default=None,
                        help="akhir periode; bawaan batas sensor arsip")
    parser.add_argument("--step", type=int, default=DEFAULT_STEP,
                        help=f"jarak antar tanggal dalam hari bursa (bawaan {DEFAULT_STEP})")
    parser.add_argument("--size", type=int, default=universe.DEFAULT_SIZE,
                        help="besar universe screener")
    parser.add_argument("--out", default=REPORT_PATH, help="tujuan laporan JSON")
    parser.add_argument("--json", action="store_true",
                        help="cetak JSON mentah, bukan tabel")
    args = parser.parse_args(argv)

    if not args.walk_forward and not args.json:
        parser.print_help()
        return 0

    data = report(start=labels.parse_date(args.start),
                  end=labels.parse_date(args.end) if args.end else None,
                  holdout=labels.parse_date(args.holdout),
                  step=args.step, size=args.size)
    path = write_report(data, args.out)
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str)
          if args.json else render(data))
    if not args.json:
        print(f"\n  laporan lengkap : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
