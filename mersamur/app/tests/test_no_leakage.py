"""Pertanyaan juri #1: apakah fiturnya melihat masa depan?

Tugas 13 §Langkah menetapkan aturannya dalam satu kalimat: **tiap fitur wajib
membawa tanggal, dan tanggal itu wajib lebih awal dari tanggal peristiwa. Fitur
tanpa tanggal dilarang masuk backtest.**

Berkas ini menjaga aturan itu di dua tingkat sekaligus, karena satu tingkat saja
selalu bisa dilewati:

  * **struktural** — tiap sumbu di `app/axes/` harus punya bidang tanggal yang
    disebutkan di tabel `DATED` di bawah, dan tabel itu harus memuat seluruh modul
    di paket itu. Sumbu baru tanpa tanggal menggagalkan tes ini pada hari ia
    ditulis, bukan pada hari juri membacanya.
  * **perilaku** — dijalankan lewat `AsOfCache(T)`, tiap tanggal yang dibawa sumbu
    harus lebih awal dari T, dan T sendiri lebih awal dari tanggal peristiwa.

`/v2/free-float/` adalah kasus ujinya yang konkret. Ia snapshot hari ini: barisnya
tidak membawa tanggal sama sekali (`riset/spec.md` §7), jadi memakainya untuk
memprediksi suspensi tahun lalu berarti membaca komposisi kepemilikan **sesudah**
peristiwanya. Penggantinya `/v2/company/shareholders-composition/` — panel bulanan
yang tiap barisnya bertanggal, jadi float bisa direkonstruksi sebagaimana ia
berdiri pada T. Dua tes di bawah membuktikan kedua sifat itu langsung dari
rekaman, bukan dari komentar.

Aturan turunan §7 yang juga dijaga di sini: suspensi tidak boleh menjadi fitur
**dan** label untuk peristiwa yang sama. Hanya suspensi sebelum jendela fitur yang
boleh menjadi fitur.

Nol kredit: seluruh berkas ini membaca `research/harness/recorded/` atau direktori
sementara. Tidak ada socket yang dibuka.
"""
import importlib
import json
import pkgutil
from datetime import date, timedelta

import pytest

from app import backtest, labels, profile, universe
from app import cache as cache_mod
from app.axes import catalyst, concentration, history, momentum, volume_anomaly
from app.backtest import AsOfCache
from app.cache import Cache

FREE_FLOAT_PATH = "/v2/free-float/"
SHAREHOLDERS_PATH = "/v2/company/shareholders-composition/BBCA/"

# Tiap sumbu, dan bidang tanggal yang wajib dibawa hasilnya. Tabel ini adalah
# kontraknya: `test_every_axis_module_is_listed_in_the_dated_table` memaksa modul
# baru di `app/axes/` masuk ke sini, jadi sumbu tanpa tanggal tidak bisa lolos
# dengan cara tidak disebut.
#
# Dua jenis tanggal, dan bedanya penting. `UKURAN` adalah hari yang benar-benar
# diukur — ia wajib **lebih awal** dari T. `BATAS` adalah bound eksklusif yang
# dibawa hasil supaya pembaca tahu sampai mana sumbu itu boleh melihat; ia sendiri
# boleh sama dengan T justru karena isinya berhenti sebelum T.
UKURAN, BATAS = "ukuran", "batas"

DATED = {
    volume_anomaly: (("start", UKURAN), ("end", UKURAN)),
    momentum: (("start", UKURAN), ("end", UKURAN)),
    concentration: (("start", UKURAN), ("end", UKURAN)),
    catalyst: (("window_start", UKURAN), ("window_end", UKURAN)),
    history: (("cutoff", BATAS), ("last_date", UKURAN)),
}

# T, dan peristiwa yang harus diprediksi tanpa melihatnya.
CUTOFF = date(2026, 3, 2)
EVENT_DATE = date(2026, 3, 9)


# --- korpus buatan -----------------------------------------------------------
def daily_rows(symbol, rows):
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in rows]


BEFORE = [("2026-02-02", 100, 1_000), ("2026-02-03", 102, 1_100),
          ("2026-02-04", 101, 900), ("2026-02-05", 105, 1_200),
          ("2026-02-06", 110, 1_500), ("2026-02-09", 118, 2_000),
          ("2026-02-10", 130, 3_000), ("2026-02-11", 128, 2_500),
          ("2026-02-12", 140, 4_000), ("2026-02-13", 155, 9_000),
          ("2026-02-17", 160, 5_000), ("2026-02-18", 175, 7_000),
          ("2026-02-19", 190, 8_000), ("2026-02-20", 205, 12_000),
          ("2026-02-23", 220, 30_000), ("2026-02-24", 240, 60_000)]
# Sesi, artikel dan panel yang seluruhnya berada **sesudah** T. Tidak satu pun
# boleh muncul di dalam fitur mana pun.
AFTER = [("2026-03-02", 300, 500_000), ("2026-03-03", 330, 900_000),
         ("2026-03-04", 360, 990_000)]

NEWS_PARAMS = {"limit": 30, "symbols": "AAAA"}
NEWS_BEFORE = [{"timestamp": "2026-02-20T09:00:00", "symbols": ["AAAA"],
                "dimension": {"technical": 1}},
               {"timestamp": "2026-02-24T09:00:00", "symbols": ["AAAA"],
                "dimension": {"technical": 1}}]
NEWS_AFTER = [{"timestamp": "2026-03-05T09:00:00", "symbols": ["AAAA"],
               "dimension": {"financials": 1, "future": 1}}]

# Panel yang jendelanya sudah tutup sebelum T, jadi ia sah sebagai fitur.
PANEL_CLOSED = {"symbol": "AAAA.JK", "start": "2025-11-03", "end": "2026-01-30",
                "top_buyers": [{"rank": 1, "broker_code": "XL", "buy_idr": 800,
                                "sell_idr": 100, "net_idr": 700},
                               {"rank": 2, "broker_code": "AT", "buy_idr": 200,
                                "sell_idr": 50, "net_idr": 150}],
                "top_sellers": [{"rank": 1, "broker_code": "DH", "buy_idr": 50,
                                 "sell_idr": 500, "net_idr": -450}]}

# Riwayat suspensi: satu jauh sebelum jendela fitur (sah sebagai fitur), satu
# tepat pada tanggal peristiwa (label — tidak boleh pernah menjadi fitur).
SUSP_PRIOR = {"symbol": "AAAA.JK", "suspension_date": "2025-05-06",
              "reason": "Dalam rangka cooling down"}
SUSP_EVENT = {"symbol": "AAAA.JK", "suspension_date": EVENT_DATE.isoformat(),
              "reason": "peningkatan harga kumulatif yang signifikan"}


def write_corpus(tmp_path, dailies=(), panels=(), news=(), suspensions=(),
                 brokers=()):
    """Rekaman kecil, ditulis persis seperti `capture.py` menulisnya."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = {}

    def add(path, params, payload):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    for symbol, params, payload in dailies:
        add(volume_anomaly.DAILY_PATH.format(symbol=symbol), params, payload)
    for symbol, params, payload in panels:
        add(concentration.BROKER_SUMMARY_PATH.format(symbol=symbol), params, payload)
    for params, payload in news:
        add(catalyst.NEWS_PATH, params, payload)
    if brokers:
        add(concentration.BROKERS_PATH, concentration.BROKERS_PARAMS,
            {"results": list(brokers)})
    add(labels.SUSPENSIONS_PATH, labels.SUSPENSIONS_PARAMS,
        {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def corpus_with_the_future(tmp_path):
    """Korpus yang memuat masa depan T, termasuk peristiwa yang harus diprediksi."""
    return write_corpus(
        tmp_path / "penuh",
        dailies=[("AAAA", {}, daily_rows("AAAA", BEFORE + AFTER))],
        panels=[("AAAA", {"n_brokers": 10}, PANEL_CLOSED)],
        news=[(NEWS_PARAMS, {"results": NEWS_BEFORE + NEWS_AFTER})],
        suspensions=[SUSP_PRIOR, SUSP_EVENT],
        brokers=[{"code": "XL", "name": "XL Sekuritas", "cohort": "retail"}])


def thresholds_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": 9, "updated_on": "2026-09-09",
           "current": {"concentration": 0.45, "volume_anomaly": 5.0,
                       "momentum": 90.0, "catalyst": 0.10},
           "bounds": {}, "cohort_factors": {}, "history": []}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def axis_results(source, thresholds_path):
    """Hasil kelima sumbu atas satu korpus, dipanggil apa adanya."""
    return {
        volume_anomaly: volume_anomaly.score("AAAA", cache=source,
                                             thresholds_path=thresholds_path),
        momentum: momentum.score("AAAA", cache=source,
                                 thresholds_path=thresholds_path),
        concentration: concentration.score("AAAA", cache=source,
                                           thresholds_path=thresholds_path),
        catalyst: catalyst.score("AAAA", cache=source),
        history: history.score("AAAA", CUTOFF, cache=source),
    }


# --- tiap fitur membawa tanggal ---------------------------------------------
def test_every_axis_module_is_listed_in_the_dated_table():
    """Sumbu baru tanpa tanggal tidak bisa lolos dengan cara tidak disebut.

    Tabel `DATED` adalah kontrak berkas ini. Kalau seseorang menambah modul sumbu
    dan tidak menuliskan bidang tanggalnya, kegagalannya muncul di sini — bukan
    diam-diam menjadi fitur tak bertanggal di dalam backtest.
    """
    import app.axes as package

    listed = {module.__name__ for module in DATED}
    found = {f"app.axes.{info.name}"
             for info in pkgutil.iter_modules(package.__path__)}
    assert found == listed, (
        f"modul sumbu tanpa entri tanggal: {sorted(found - listed)}")
    for module in DATED:
        assert importlib.import_module(module.__name__) is module


def test_every_axis_result_carries_a_parseable_date(tmp_path):
    """Bidang tanggalnya harus terisi dan terbaca, bukan string kosong."""
    source = AsOfCache(CUTOFF, source=corpus_with_the_future(tmp_path))
    results = axis_results(source, thresholds_file(tmp_path / "bar"))
    for module, fields in DATED.items():
        result = results[module]
        for field, _kind in fields:
            value = getattr(result, field)
            assert value, f"{module.__name__}.{field} kosong"
            assert labels.parse_date(value) is not None, (
                f"{module.__name__}.{field} = {value!r} tidak terbaca sebagai tanggal")


def test_every_feature_date_precedes_the_event_it_must_predict(tmp_path):
    """Aturan tugas 13, diuji langsung: tiap tanggal fitur < T <= tanggal peristiwa.

    Korpusnya sengaja memuat sesi 2026-03, artikel 2026-03-05 dan pengumuman
    suspensi 2026-03-09. Kalau `AsOfCache` bocor di salah satu endpoint, salah satu
    tanggal di bawah akan melewati T dan tesnya menyebut sumbu mana.
    """
    source = AsOfCache(CUTOFF, source=corpus_with_the_future(tmp_path))
    results = axis_results(source, thresholds_file(tmp_path / "bar"))
    assert CUTOFF <= EVENT_DATE
    for module, fields in DATED.items():
        for field, kind in fields:
            when = labels.parse_date(getattr(results[module], field))
            limit = CUTOFF if kind == UKURAN else CUTOFF + timedelta(days=1)
            assert when < limit, (
                f"{module.__name__}.{field} = {when} melewati T={CUTOFF}")
            assert when < EVENT_DATE


def test_the_guarded_axes_still_measure_something(tmp_path):
    """Kontrol: penjaga yang mengosongkan korpus lulus semua tes di atas.

    Tanpa ini, implementasi yang menolak seluruh payload akan terbaca sempurna —
    tidak ada tanggal yang melewati T karena tidak ada tanggal sama sekali.
    """
    source = AsOfCache(CUTOFF, source=corpus_with_the_future(tmp_path))
    results = axis_results(source, thresholds_file(tmp_path / "bar"))
    assert results[volume_anomaly].n_sessions == len(BEFORE)
    assert results[momentum].percentile is not None
    assert results[concentration].top1_ratio is not None
    assert results[catalyst].n_articles == len(NEWS_BEFORE)
    assert results[history].n_prior == 1


# --- free float: fitur tanpa tanggal ----------------------------------------
def test_the_recorded_free_float_payload_carries_no_date_at_all():
    """Alasan larangannya, dibaca dari payload yang sudah dibayar 10 kredit.

    Tidak ada `date`, `timestamp`, `period`, atau apa pun yang menempatkan angka
    ini di sebuah hari. Ia adalah komposisi hari ini, dan hari ini datang sesudah
    tiap peristiwa di dalam backtest.
    """
    hit = Cache().get(FREE_FLOAT_PATH, {})
    assert hit is not None and hit.found, (
        "rekaman /v2/free-float/ hilang dari research/harness/recorded/")
    rows = hit.payload if isinstance(hit.payload, list) else hit.payload.get("results")
    assert rows, "payload free-float kosong"
    keys = {k.lower() for row in rows if isinstance(row, dict) for k in row}
    assert keys, "baris free-float tanpa bidang apa pun"
    assert not any("date" in k or "time" in k or "period" in k or "year" in k
                   for k in keys), f"free-float ternyata membawa tanggal: {sorted(keys)}"


def test_free_float_is_withheld_by_the_backtest_gate():
    """Pintu ke masa lalu menahannya, dan mencatat bahwa ia menahannya.

    Ditahan, bukan diloloskan sebagai referensi tak bertanggal: daftar broker dan
    baris screener boleh lewat karena keduanya keanggotaan, sedangkan free float
    adalah **pengukuran** yang tanggalnya tidak diketahui.
    """
    source = AsOfCache(CUTOFF, source=Cache())
    assert source.get(FREE_FLOAT_PATH, {}) is None
    assert FREE_FLOAT_PATH in source.withheld_paths
    assert FREE_FLOAT_PATH not in AsOfCache.UNDATED_REFERENCE
    assert set(AsOfCache.UNDATED_REFERENCE) == {universe.SCREENER_PATH,
                                                concentration.BROKERS_PATH}


def test_no_axis_cites_free_float_as_a_source():
    """Larangan struktural: tidak ada sumbu yang boleh mengaku membacanya.

    `profile.SOURCES` adalah daftar sitasi yang tampil di layar. Sebuah sumbu yang
    memakai free float harus menuliskannya di sana untuk bisa disitasi, jadi
    melarangnya di sini melarang pemakaiannya secara terbuka.
    """
    for axis, sources in profile.SOURCES.items():
        for source in sources:
            assert FREE_FLOAT_PATH not in source.endpoint, (
                f"sumbu {axis} menyitasi free float, yang tidak bertanggal")


def test_every_cited_measurement_source_names_a_dated_field():
    """Tiap endpoint yang diukur harus menyebut bidang yang menempatkannya di waktu.

    Ini yang membuat larangan free float menjadi aturan, bukan daftar hitam satu
    baris: endpoint tak bertanggal apa pun gagal di sini begitu ia disitasi.
    """
    dated = ("date", "timestamp", "suspension_date", "start", "end")
    for axis, sources in profile.SOURCES.items():
        api = [s for s in sources if s.origin == "api"]
        assert api, f"sumbu {axis} tidak menyitasi endpoint apa pun"
        measurement = api[0]
        assert any(field in dated for field in measurement.fields), (
            f"sumbu {axis} membaca {measurement.endpoint} tanpa bidang bertanggal: "
            f"{measurement.fields}")


def test_the_dated_replacement_can_be_cut_at_t():
    """Penggantinya: float direkonstruksi dari panel kepemilikan bulanan.

    Tiap baris `shareholders-composition` membawa `date`, jadi komposisi pada T
    adalah baris terbaru yang tanggalnya lebih awal dari T — persis operasi yang
    tidak mungkin dilakukan pada free float. Diuji atas rekaman nyata.
    """
    hit = Cache().get(SHAREHOLDERS_PATH, {})
    assert hit is not None and hit.found, (
        "rekaman shareholders-composition BBCA hilang dari recorded/")
    rows = hit.payload.get("data") or []
    assert len(rows) > 1, "panel kepemilikan hanya punya satu baris"
    dates = [labels.parse_date(row.get("date")) for row in rows]
    assert all(when is not None for when in dates), (
        "ada baris kepemilikan tanpa tanggal yang terbaca")

    as_of = max(dates)
    visible = [when for when in dates if when < as_of]
    assert visible, "tidak ada baris yang lebih awal dari baris terbaru"
    assert max(visible) < as_of
    # Bulanan, bukan snapshot tunggal: jarak antar baris terhitung dalam minggu.
    assert (as_of - max(visible)).days >= 20


# --- suspensi: fitur atau label, tidak keduanya ------------------------------
def test_the_event_being_predicted_never_becomes_a_feature(tmp_path):
    """§7: suspensi tidak boleh jadi fitur **dan** label untuk peristiwa yang sama.

    Sumbu riwayat dipanggil dengan cutoff = hari pertama jendela fitur, jadi
    pengumuman 2026-03-09 — labelnya — tidak boleh terhitung, dan begitu juga
    apa pun yang terjadi antara jendela dan peristiwanya.
    """
    source = corpus_with_the_future(tmp_path)
    at_window_start = history.score("AAAA", date(2026, 2, 2), cache=source)
    assert at_window_start.n_prior == 1
    assert at_window_start.last_date == SUSP_PRIOR["suspension_date"]
    assert EVENT_DATE.isoformat() not in [e.date.isoformat()
                                          for e in history.prior_events(
                                              "AAAA", date(2026, 2, 2), cache=source)]


def test_history_without_a_cutoff_raises_instead_of_defaulting_to_today():
    """Default "hari ini" di sini adalah kebocoran yang tidak terlihat di layar."""
    with pytest.raises(ValueError):
        history.prior_events("AAAA", None)
    with pytest.raises(ValueError):
        labels.history_before("AAAA", None)


def test_the_profile_window_closes_before_t(tmp_path):
    """Permukaan yang dibaca orang membawa jendelanya sendiri, dan jendela itu tutup."""
    result = profile.build("AAAA",
                           cache=AsOfCache(CUTOFF, source=corpus_with_the_future(tmp_path)),
                           cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"),
                           as_of=CUTOFF.isoformat())
    assert labels.parse_date(result.window_end) < CUTOFF
    assert labels.parse_date(result.window_start) < labels.parse_date(result.window_end)
    assert labels.parse_date(result.cutoff) <= CUTOFF


def test_the_walk_forward_reports_what_it_withheld(tmp_path):
    """Yang ditahan harus terbaca di laporan, bukan hilang tanpa jejak.

    Sebuah payload tak bertanggal yang ditahan diam-diam terlihat sama persis
    dengan sumbu yang memang tidak punya data. Backtest menuliskannya.
    """
    corpus = corpus_with_the_future(tmp_path)
    source = AsOfCache(CUTOFF, source=corpus)
    assert source.get(FREE_FLOAT_PATH, {}) is None
    row = backtest.run_date(CUTOFF, ["AAAA"], cache=corpus,
                            thresholds_path=thresholds_file(tmp_path / "bar"))
    assert isinstance(row.withheld, tuple)
    assert row.horizon_start > row.when
