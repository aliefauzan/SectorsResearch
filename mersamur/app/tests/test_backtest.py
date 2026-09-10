"""Apa yang tidak boleh dilakukan sebuah backtest: melihat masa depan, atau memolesnya.

Sumbu-sumbunya sudah diuji satu per satu dan `evaluate.score()` sudah diuji sebagai
satu-satunya pembangun confusion matrix. Berkas ini menguji **sumbu waktu** yang
ditambahkan tugas 12 di luarnya, dan tiap tes membidik satu implementasi keliru yang
kalau tidak diuji akan terlihat benar:

  * **fitur yang melihat melewati T.** Tes utama yang diminta tugas 12: profil pada
    tanggal T harus identik entah data sesudah T dipotong oleh `AsOfCache` atau
    memang tidak pernah ada di dalam korpus. Diuji dengan membangun dua korpus,
    bukan dengan mempercayai komentar.
  * **payload yang tidak bisa dipotong tapi diloloskan.** Panel broker adalah agregat
    satu jendela. Meloloskannya berarti sumbu konsentrasi pada 2025 membaca nilai
    transaksi Agustus 2026.
  * **jendela hasil yang memuat T sendiri.** Peristiwa bertanggal T sudah terjadi
    saat keputusan diambil; menghitungnya sebagai hasil adalah kebocoran yang
    grafiknya paling indah.
  * **tanggal yang hasilnya belum bisa diamati.** Sesudah batas sensor, nol berarti
    arsipnya habis, bukan tidak terjadi apa-apa.
  * **rumus lift kedua.** Matriks tetap hanya dibangun di `evaluate.score()` dan
    penggabungannya harus penjumlahan murni.
  * **laporan yang diam ketika hasilnya buruk.** §6 meminta temuan negatif ditulis;
    ada tes yang memaksanya muncul.
  * **vonis.** Tidak ada beli/jual, skor sebagai anjuran, atau warna.

Nol kredit: seluruh tes membaca `research/harness/recorded/` atau direktori
sementara. Tidak ada socket yang dibuka.
"""
import ast
import json
import re
from datetime import date, timedelta

import pytest

from app import backtest, baselines, config, evaluate, labels, profile, universe
from app import cache as cache_mod
from app.axes import catalyst, concentration, history, volume_anomaly
from app.backtest import AsOfCache, SPLIT_HOLDOUT, SPLIT_TUNING
from app.cache import Cache


# --- korpus buatan -----------------------------------------------------------
def daily_rows(symbol, rows):
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in rows]


def write_corpus(tmp_path, dailies=(), panels=(), news=(), suspensions=(),
                 brokers=(), screener=None):
    """Rekaman kecil, ditulis persis seperti `capture.py` menulisnya.

    Satu berkas payload per slug plus baris manifest, supaya tes menempuh jalur
    pencarian yang sama dengan produk dan bukan jalan pintas khusus tes.
    """
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
    if screener is not None:
        add(universe.SCREENER_PATH, universe.SCREENER_PARAMS,
            {"results": list(screener)})
    add(labels.SUSPENSIONS_PATH, labels.SUSPENSIONS_PARAMS,
        {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def thresholds_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": 9, "updated_on": "2026-09-09",
           "current": {"concentration": 0.45, "volume_anomaly": 5.0,
                       "momentum": 90.0, "catalyst": 0.10},
           "bounds": {}, "cohort_factors": {}, "history": []}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


CUTOFF = date(2026, 3, 2)

# Sesi sebelum cutoff, lalu sesi sesudahnya. Kedua korpus di bawah berbagi bagian
# pertama; hanya korpus "penuh" yang memuat bagian kedua.
BEFORE = [("2026-02-02", 100, 1_000), ("2026-02-03", 102, 1_100),
          ("2026-02-04", 101, 900), ("2026-02-05", 105, 1_200),
          ("2026-02-06", 110, 1_500), ("2026-02-09", 118, 2_000),
          ("2026-02-10", 130, 3_000), ("2026-02-11", 128, 2_500),
          ("2026-02-12", 140, 4_000), ("2026-02-13", 155, 9_000),
          ("2026-02-17", 160, 5_000), ("2026-02-18", 175, 7_000),
          ("2026-02-19", 190, 8_000), ("2026-02-20", 205, 12_000),
          ("2026-02-23", 220, 30_000), ("2026-02-24", 240, 60_000)]
AFTER = [("2026-03-02", 300, 500_000), ("2026-03-03", 330, 900_000),
         ("2026-03-04", 360, 990_000)]

NEWS_BEFORE = [{"timestamp": "2026-02-20T09:00:00", "symbols": ["AAAA"],
                "dimension": {"technical": 1}},
               {"timestamp": "2026-02-24T09:00:00", "symbols": ["AAAA"],
                "dimension": {"technical": 1}}]
NEWS_AFTER = [{"timestamp": "2026-03-05T09:00:00", "symbols": ["AAAA"],
               "dimension": {"financials": 1, "future": 1}}]

SUSP_BEFORE = [{"symbol": "AAAA.JK", "suspension_date": "2025-05-06",
                "reason": "Dalam rangka cooling down"}]
SUSP_AFTER = [{"symbol": "AAAA.JK", "suspension_date": "2026-03-09",
               "reason": "peningkatan harga kumulatif yang signifikan"}]

NEWS_PARAMS = {"limit": 30, "symbols": "AAAA"}


def full_corpus(tmp_path):
    """Korpus yang memuat masa depan: sesi, artikel dan suspensi sesudah cutoff."""
    return write_corpus(
        tmp_path / "penuh",
        dailies=[("AAAA", {}, daily_rows("AAAA", BEFORE + AFTER))],
        news=[(NEWS_PARAMS, {"results": NEWS_BEFORE + NEWS_AFTER})],
        suspensions=SUSP_BEFORE + SUSP_AFTER)


def truncated_corpus(tmp_path):
    """Korpus yang masa depannya benar-benar dihapus dari berkasnya."""
    return write_corpus(
        tmp_path / "terpotong",
        dailies=[("AAAA", {}, daily_rows("AAAA", BEFORE))],
        news=[(NEWS_PARAMS, {"results": NEWS_BEFORE})],
        suspensions=SUSP_BEFORE)


def readings_of(result):
    """Nilai, keadaan dan ambang tiap sumbu — bagian profil yang bukan jam dinding."""
    return [(r.axis, r.value, r.state, r.threshold, r.unknown_reason)
            for r in result.readings + result.supporting]


# --- tes utama tugas 12 ------------------------------------------------------
def test_features_at_t_do_not_change_when_later_data_is_deleted(tmp_path):
    """Tes yang diminta tugas 12 §Kriteria selesai, dan alasan AsOfCache ada.

    Kalau `AsOfCache` bocor, profil dari korpus penuh akan berbeda dari profil korpus
    yang masa depannya memang tidak ada — sesi 2026-03 akan menaikkan volume, harga
    dan persentil momentum, dan artikel fundamental 2026-03-05 akan mematikan sumbu
    katalis. Tesnya membandingkan keduanya, bukan mempercayai komentar.
    """
    bars = thresholds_file(tmp_path / "bar")
    lewat = profile.build("AAAA", cache=AsOfCache(CUTOFF, source=full_corpus(tmp_path)),
                          cutoff=CUTOFF, thresholds_path=bars, as_of="2026-03-02")
    tanpa = profile.build("AAAA", cache=truncated_corpus(tmp_path), cutoff=CUTOFF,
                          thresholds_path=bars, as_of="2026-03-02")
    assert readings_of(lewat) == readings_of(tanpa)
    assert lewat.axes_fired == tanpa.axes_fired
    assert lewat.window_end == tanpa.window_end == "2026-02-24"


def test_deleting_later_data_changes_the_profile_when_the_guard_is_removed(tmp_path):
    """Kontrol untuk tes di atas: kalau tidak ada yang dipotong, hasilnya berubah.

    Tanpa ini, tes kembar di atas akan tetap lulus pada implementasi yang membuang
    seluruh payload dan membuat setiap sumbu `tidak_diketahui` — dua profil kosong
    yang identik dan tidak membuktikan apa pun.
    """
    bars = thresholds_file(tmp_path / "bar")
    penuh = profile.build("AAAA", cache=full_corpus(tmp_path), cutoff=CUTOFF,
                          thresholds_path=bars, as_of="2026-03-02")
    tanpa = profile.build("AAAA", cache=truncated_corpus(tmp_path), cutoff=CUTOFF,
                          thresholds_path=bars, as_of="2026-03-02")
    assert readings_of(penuh) != readings_of(tanpa)
    assert penuh.window_end == "2026-03-04"


def test_the_guarded_profile_still_measures_something(tmp_path):
    """`AsOfCache` memotong masa depan, bukan seluruh data.

    Sebuah "leak guard" yang mengosongkan korpus lulus setiap tes kebocoran dan tidak
    mengukur apa pun. Di sini sumbu harga harus tetap terukur pada T.
    """
    result = profile.build("AAAA", cache=AsOfCache(CUTOFF, source=full_corpus(tmp_path)),
                           cutoff=CUTOFF, thresholds_path=thresholds_file(tmp_path / "bar"))
    measured = [r.axis for r in result.readings if r.fired is not None]
    assert "volume_anomaly" in measured and "momentum" in measured
    assert result.window_start == "2026-02-02"


# --- AsOfCache, aturan per endpoint -----------------------------------------
def test_suspension_archive_is_cut_at_the_cutoff(tmp_path):
    """Label yang belum terjadi tidak boleh terlihat sebagai riwayat."""
    source = AsOfCache(CUTOFF, source=full_corpus(tmp_path))
    seen = labels.load_events(cache=source)
    assert [e.date.isoformat() for e in seen] == ["2025-05-06"]
    assert history.score("AAAA", CUTOFF, cache=source).n_prior == 1


def test_an_uncuttable_window_aggregate_is_withheld_not_passed(tmp_path):
    """Panel broker berjendela 2026-06..2026-09 tidak boleh terbaca pada Maret 2026."""
    panel = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09",
             "top_buyers": [{"rank": 1, "broker_code": "XL", "buy_idr": 100,
                             "net_idr": 90, "sell_idr": 10}],
             "top_sellers": []}
    corpus = write_corpus(tmp_path / "panel",
                          panels=[("AAAA", {"n_brokers": 10}, panel)])
    source = AsOfCache(CUTOFF, source=corpus)
    with pytest.raises(concentration.NoBrokerDataError):
        concentration.panel("AAAA", cache=source)
    assert any("broker-summary" in p for p in source.withheld_paths)


def test_a_window_aggregate_that_closed_before_t_is_admitted(tmp_path):
    """Aturannya jendela, bukan larangan menyeluruh: panel yang sudah tutup boleh."""
    panel = {"symbol": "AAAA.JK", "start": "2025-11-01", "end": "2026-01-30",
             "top_buyers": [{"rank": 1, "broker_code": "XL", "buy_idr": 100,
                             "net_idr": 90, "sell_idr": 10}],
             "top_sellers": []}
    corpus = write_corpus(tmp_path / "panel2",
                          panels=[("AAAA", {"n_brokers": 10}, panel)])
    source = AsOfCache(CUTOFF, source=corpus)
    assert concentration.panel("AAAA", cache=source)["end"] == "2026-01-30"
    assert not source.withheld_paths


def test_an_unknown_dated_path_fails_closed(tmp_path):
    """Payload tanpa aturan pemotongan ditahan, bukan diloloskan diam-diam."""
    corpus = write_corpus(tmp_path / "asing")
    source = AsOfCache(CUTOFF, source=corpus)
    assert source.get("/v2/filings/", {}) is None
    corpus_with = write_corpus(tmp_path / "asing2")
    # Path yang memang ada di manifest tapi tak berbentuk apa pun yang dikenali.
    key = cache_mod.slug("/v2/filings/", {})
    manifest = json.loads((tmp_path / "asing2" / "_manifest.json").read_text())
    manifest[key] = {"path": "/v2/filings/", "params": {}, "status": 200}
    (tmp_path / "asing2" / f"{key}.json").write_text('{"results": []}')
    (tmp_path / "asing2" / "_manifest.json").write_text(json.dumps(manifest))
    source2 = AsOfCache(CUTOFF, source=Cache(root=str(tmp_path / "asing2")))
    assert source2.get("/v2/filings/", {}) is None
    assert "/v2/filings/" in source2.withheld_paths


def test_undated_reference_data_passes_through(tmp_path):
    """Daftar broker dan baris screener tidak bertanggal: menahannya mematikan universe."""
    corpus = write_corpus(
        tmp_path / "ref",
        brokers=[{"code": "XL", "name": "XL Sekuritas", "cohort": "retail"}],
        screener=[{"symbol": "AAAA.JK", "company_name": "A",
                   "query_values": {"market_cap": 1}}])
    source = AsOfCache(CUTOFF, source=corpus)
    assert concentration.registry(cache=source)
    assert universe.watchlist(cache=source) == ["AAAA"]


def test_a_settled_404_stays_a_404(tmp_path):
    """404 yang sudah dibayar tidak bertanggal: ia tetap jawaban yang sama kapan pun."""
    tmp = tmp_path / "gone"
    tmp.mkdir(parents=True, exist_ok=True)
    key = cache_mod.slug("/v2/daily/ZZZZ/", {})
    (tmp / "_manifest.json").write_text(json.dumps(
        {key: {"path": "/v2/daily/ZZZZ/", "params": {}, "status": 404}}))
    source = AsOfCache(CUTOFF, source=Cache(root=str(tmp)))
    hit = source.get("/v2/daily/ZZZZ/", {})
    assert hit is not None and hit.status == 404 and not hit.found


def test_as_of_cache_needs_a_date():
    """Tanpa tanggal tidak ada batas kebocoran, jadi ini gagal keras."""
    with pytest.raises(ValueError):
        AsOfCache(None)


# --- jendela hasil ----------------------------------------------------------
def test_horizon_opens_after_t_and_spans_trading_days():
    """Terbuka di T: peristiwa bertanggal T sudah terjadi saat keputusan diambil."""
    first, last = backtest.horizon(date(2026, 9, 1), sessions=10)
    assert first > date(2026, 9, 1)
    assert config.is_trading_day(first) and config.is_trading_day(last)
    assert len(backtest.trading_days_forward(date(2026, 9, 1), 10)) == 10


def test_horizon_skips_holidays_rather_than_counting_them():
    """17 Agustus 2026 libur bursa; jendela 10 sesi harus melewatinya, bukan memakainya."""
    days = backtest.trading_days_forward(date(2026, 8, 12), 10)
    assert date(2026, 8, 17) not in days
    assert len(days) == 10


def test_an_event_dated_on_t_is_not_an_outcome(tmp_path):
    """Kebocoran yang grafiknya paling indah: menghitung hari keputusan sebagai hasil."""
    corpus = write_corpus(tmp_path / "ev", suspensions=SUSP_AFTER)
    event_day = date(2026, 3, 9)
    assert "AAAA" not in backtest.outcomes(["AAAA"], event_day, cache=corpus)
    assert "AAAA" in backtest.outcomes(["AAAA"], event_day - timedelta(days=3),
                                       cache=corpus)


def test_an_event_beyond_the_horizon_is_not_an_outcome(tmp_path):
    """10 sesi adalah 10 sesi. Peristiwa dua bulan kemudian bukan hasil tanggal ini."""
    corpus = write_corpus(tmp_path / "ev2", suspensions=SUSP_AFTER)
    assert not backtest.outcomes(["AAAA"], date(2026, 1, 5), cache=corpus)


def test_only_the_label_class_counts_as_an_outcome(tmp_path):
    """Delapan kelas lain adalah riwayat, bukan target (`app.labels` §Q4)."""
    corpus = write_corpus(tmp_path / "kelas", suspensions=[
        {"symbol": "AAAA.JK", "suspension_date": "2026-03-09",
         "reason": "belum menyampaikan laporan keuangan"}])
    assert not backtest.outcomes(["AAAA"], date(2026, 3, 2), cache=corpus)


def test_pre_2025_events_are_never_outcomes(tmp_path):
    """Nol suspensi cooling-down sebelum 2025; tugas 12 §2 melarang menyentuhnya."""
    corpus = write_corpus(tmp_path / "lama", suspensions=[
        {"symbol": "AAAA.JK", "suspension_date": "2024-03-06",
         "reason": "Dalam rangka cooling down"}])
    assert not backtest.outcomes(["AAAA"], date(2024, 3, 2), cache=corpus)


# --- sensor ------------------------------------------------------------------
def test_dates_whose_outcome_cannot_be_observed_are_dropped():
    """Sesudah batas sensor, nol berarti arsipnya habis — bukan tidak terjadi apa-apa."""
    limit = backtest.censoring_limit()
    archive = labels.load_events()
    assert limit is not None and limit < archive[-1].date
    assert backtest.horizon(limit)[1] <= archive[-1].date
    assert backtest.horizon(limit + timedelta(days=1))[1] > archive[-1].date


def test_the_grid_holds_only_trading_days():
    days = backtest.grid(date(2026, 8, 1), date(2026, 8, 31), step=1)
    assert days and all(config.is_trading_day(d) for d in days)
    assert date(2026, 8, 17) not in days


def test_the_grid_step_thins_without_reordering():
    every = backtest.grid(date(2026, 8, 1), date(2026, 8, 31), step=1)
    weekly = backtest.grid(date(2026, 8, 1), date(2026, 8, 31), step=5)
    assert weekly == every[::5]


# --- penggabungan matriks ----------------------------------------------------
def test_pooling_is_addition_and_nothing_else():
    """Tidak ada rumus lift kedua di repo ini: `pool` hanya menjumlahkan."""
    a = evaluate.Result(system="x", n=10, warnings=3, tp=1, fp=2, fn=1, tn=6,
                        base_rate=0.2)
    b = evaluate.Result(system="x", n=20, warnings=5, tp=2, fp=3, fn=3, tn=12,
                        base_rate=0.25)
    merged = backtest.pool("x", [a, b])
    assert (merged.n, merged.warnings, merged.tp, merged.fp, merged.fn, merged.tn) \
        == (30, 8, 3, 5, 4, 18)
    assert merged.base_rate == pytest.approx((3 + 4) / 30)
    assert merged.precision == pytest.approx(3 / 8)
    assert merged.lift == pytest.approx(merged.precision / merged.base_rate)


def test_pooled_lift_is_undefined_not_zero_when_nothing_warned():
    """Aturan yang sama dengan tugas 11: nol peringatan adalah pengukuran yang absen."""
    empty = evaluate.Result(system="x", n=10, warnings=0, tp=0, fp=0, fn=2, tn=8,
                            base_rate=0.2)
    merged = backtest.pool("x", [empty, empty])
    assert merged.lift is None and merged.precision is None


def test_the_confusion_matrix_is_only_built_in_evaluate():
    """Sumbu waktu ditambahkan di luar jalur penilaian, tidak menggantikannya.

    Diperiksa dengan mem-parse berkasnya: `backtest.py` boleh memanggil
    `evaluate.score_all` dan `evaluate.contenders`, tapi tidak boleh mendefinisikan
    kelas hasil atau fungsi penilaiannya sendiri. Dua jalur penilaian membuat
    perbandingan tugas 11 dan tugas 12 tidak sebanding, dan itu persis yang
    `tasks/11` §1 sebut sebagai alasan membatalkan perbandingan.
    """
    tree = ast.parse(open(backtest.__file__, encoding="utf-8").read())
    defined = {n.name for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert "score" not in defined and "score_all" not in defined
    assert "Result" not in defined and "conditional_lift" not in defined

    called = {f"{getattr(n.func.value, 'id', '')}.{n.func.attr}"
              for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute)}
    assert "evaluate.score_all" in called
    assert "evaluate.contenders" in called


# --- laporan -----------------------------------------------------------------
@pytest.fixture(scope="module")
def small_report():
    """Satu jalankan kecil atas rekaman sungguhan. Cukup untuk memeriksa bentuknya."""
    return backtest.report(start=date(2026, 6, 1), end=date(2026, 8, 26),
                           holdout=date(2026, 7, 1), step=10, size=25)


def test_report_carries_both_splits_and_both_baselines(small_report):
    """§Kriteria selesai: lift penyetelan, lift hold-out, berdampingan dengan keduanya."""
    for name in (SPLIT_TUNING, SPLIT_HOLDOUT):
        results = small_report["splits"][name]["results"]
        assert evaluate.SYSTEM in results
        for rival in baselines.NAMES:
            assert rival in results
            assert "lift" in results[rival]


def test_report_carries_the_full_confusion_matrix(small_report):
    for split in small_report["splits"].values():
        for row in split["results"].values():
            assert {"tp", "fp", "fn", "tn", "n", "warnings"} <= set(row)


def test_report_splits_by_regime_year(small_report):
    """§4: base rate 2025 dan 2026 berbeda, jadi keduanya dilaporkan terpisah."""
    assert small_report["regimes"]
    assert all(key.isdigit() for key in small_report["regimes"])


def test_report_records_its_own_parameters_and_windows(small_report):
    p = small_report["parameters"]
    assert p["holdout"] == "2026-07-01"
    assert p["horizon_hari_bursa"] == backtest.HORIZON_SESSIONS
    assert p["step_hari_bursa"] == 10
    assert p["holdout_dipakai_menyetel"] is False
    assert p["thresholds_version"] is not None


def test_report_counts_events_per_split(small_report):
    total = sum(row["n_peristiwa"] for row in small_report["per_tanggal"])
    assert total == sum(small_report["splits"][name]["n_peristiwa"]
                        for name in (SPLIT_TUNING, SPLIT_HOLDOUT))


def test_report_states_the_negative_finding_rather_than_hiding_it(small_report):
    """§6: kalau hold-out tidak lebih baik dari baseline, itu ditulis di laporan."""
    holdout = small_report["splits"][SPLIT_HOLDOUT]["results"][evaluate.SYSTEM]
    temuan = " ".join(small_report["temuan"]).lower()
    assert small_report["temuan"]
    if holdout["lift"] is None:
        assert "tidak terdefinisi" in temuan
    else:
        assert evaluate.SYSTEM in temuan
    assert "hold-out tidak dipakai untuk memilih apa pun" in temuan


def test_report_names_what_it_withheld_and_what_it_cannot_fix(small_report):
    """Angka yang tidak terukur harus punya sebab tertulis, bukan hilang begitu saja."""
    assert small_report["batas"]
    assert any("panel broker" in note.lower() for note in small_report["batas"])
    assert any("screener" in note.lower() for note in small_report["batas"])


def test_holdout_dates_are_all_on_or_after_the_boundary(small_report):
    boundary = labels.parse_date(small_report["parameters"]["holdout"])
    tuning_dates = small_report["splits"][SPLIT_TUNING]["n_tanggal"]
    holdout_dates = small_report["splits"][SPLIT_HOLDOUT]["n_tanggal"]
    assert tuning_dates + holdout_dates == small_report["grid"]["n_tanggal"]
    for row in small_report["per_tanggal"]:
        when = labels.parse_date(row["tanggal"])
        expected = SPLIT_HOLDOUT if when >= boundary else SPLIT_TUNING
        assert backtest.split_of(when, boundary) == expected


def test_report_is_written_whole(tmp_path, small_report):
    path = backtest.write_report(small_report, str(tmp_path / "backtest_report.json"))
    reloaded = json.loads(open(path, encoding="utf-8").read())
    assert reloaded["parameters"] == small_report["parameters"]
    assert reloaded["splits"].keys() == small_report["splits"].keys()


# --- keluaran deskriptif -----------------------------------------------------
# Dicocokkan sebagai kata utuh, bukan substring: "rekaman" memuat "aman" dan
# "membeli" memuat "beli", dan keduanya kalimat yang memang harus ada.
FORBIDDEN = ("beli", "jual", "rekomendasi", "sinyal", "aman", "berbahaya",
             "merah", "hijau", "waspada", "hindari")


def test_the_rendered_report_gives_no_verdict(small_report):
    """Tidak ada vonis, warna, atau anjuran tindakan — aturan produk, bukan gaya."""
    text = backtest.render(small_report).lower()
    for word in FORBIDDEN:
        assert not re.search(rf"\b{word}\b", text), word


def test_the_rendered_report_shows_an_undefined_lift_as_a_dash():
    """`0,00x` akan terbaca sebagai kekalahan terukur; `-` berarti tidak ada ukuran."""
    assert backtest._lift(None) == "-"
    assert backtest._lift(1.5) == "1,50x"


def test_the_rendered_report_names_both_splits(small_report):
    text = backtest.render(small_report)
    assert "SET PENYETELAN" in text and "HOLD-OUT" in text
    assert "PER REZIM TAHUN" in text


def test_no_socket_is_opened_by_this_module():
    """Nol kredit bukan janji: klien HTTP tidak boleh diimpor di jalur ini.

    Diperiksa lewat pohon impor, bukan lewat pencarian teks: docstring modul ini
    menyebut `SectorsClient` justru untuk mengatakan bahwa ia tidak dipakai, dan tes
    yang mencari substring akan menghukum kalimat itu.
    """
    tree = ast.parse(open(backtest.__file__, encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
            imported.update(f"{node.module}.{a.name}" for a in node.names)
    assert not any("sectors_client" in name or "http" in name or "socket" in name
                   or "urllib" in name for name in imported), sorted(imported)
