"""Pertanyaan juri #3: apakah deret nol dibaca sebagai halt, bukan sebagai sepi?

`research/docs/api/10-domain-pitfalls.md` §2: saham yang disuspensi IDX tidak
mengembalikan error. Ia mengembalikan deret yang rapi, valid, dan **nol
seluruhnya**. Diberi makan ke penilai apa pun, baris itu terbaca sebagai outlier
ekstrem atau menarik ambang seluruh universe.

Aturan tugas 13: saham dengan seluruh fitur hitung persis nol adalah saham
**tersuspensi**, bukan sepi — dan pipeline harus mengecek `/v2/suspensions/`
sebelum menyimpulkan apa pun tentang deret datar.

Sumbunya sudah diuji satu per satu di `test_volume_momentum.py` dan
`test_concentration.py`. Yang diuji di sini adalah **pipeline**-nya, karena di
situlah kesalahannya bersembunyi: sumbu boleh benar sementara profil, matriks dan
peringatan tetap memperlakukan lubang data sebagai temuan. Empat tingkat dijaga
sekaligus:

  1. arsip suspensi benar-benar dibaca sebelum kesimpulan diambil — dibuktikan
     dengan mencatat tiap `get()` yang dilakukan, bukan dengan mempercayai
     komentar;
  2. profil menyebut halt-nya dan tidak menyalakan satu sumbu pun;
  3. kontrol: saham yang sepi tapi masih diperdagangkan tidak boleh ikut disebut
     tersuspensi — penjaga yang menyebut semuanya halt tidak menjaga apa pun;
  4. saham yang di-halt tidak pernah menjadi peringatan di jalur penilaian.

Ditambah aturan turunan `riset/spec.md` §7: pengumuman di dalam jendela adalah
**bukti** tentang lubang datanya, bukan fitur. Ia tidak boleh masuk ke sumbu
riwayat untuk jendela yang sama.

Nol kredit: seluruh berkas ini membaca direktori sementara. Tidak ada socket yang
dibuka.
"""
import json
from datetime import date

from app import evaluate, labels, profile
from app import cache as cache_mod
from app.axes import concentration, momentum, volume_anomaly
from app.cache import Cache

# Sepuluh sesi bursa berturut-turut, semuanya di dalam satu jendela.
DATES = ["2026-08-10", "2026-08-11", "2026-08-12", "2026-08-13", "2026-08-14",
         "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24"]
CUTOFF = date(2026, 8, 10)

HALT = {"symbol": "AAAA.JK", "suspension_date": "2026-08-11",
        "reason": "peningkatan harga kumulatif yang signifikan"}
OLD_HALT = {"symbol": "AAAA.JK", "suspension_date": "2025-04-02",
            "reason": "Dalam rangka cooling down"}

BROKERS = [{"code": "XL", "name": "XL Sekuritas", "cohort": "retail"},
           {"code": "DH", "name": "Sinarmas Sekuritas", "cohort": "institutional"}]


# --- korpus buatan -----------------------------------------------------------
def daily_rows(symbol, dates, closes, volumes):
    return [{"symbol": f"{symbol}.JK", "date": d, "close": c, "open": c,
             "high": c, "low": c, "volume": v, "market_cap": c * 1_000_000}
            for d, c, v in zip(dates, closes, volumes)]


def broker_rows(triples):
    return [{"rank": i + 1, "broker_code": code, "buy_idr": buy, "sell_idr": sell,
             "net_idr": buy - sell}
            for i, (code, buy, sell) in enumerate(triples)]


def panel_payload(buyers, sellers, start="2026-08-10", end="2026-08-24"):
    return {"symbol": "AAAA.JK", "start": start, "end": end,
            "top_buyers": broker_rows(buyers), "top_sellers": broker_rows(sellers)}


LIVE_PANEL = panel_payload([("XL", 900_000_000, 100_000_000),
                            ("DH", 100_000_000, 50_000_000)],
                           [("DH", 50_000_000, 400_000_000)])
# Panel yang seluruh nilainya nol: tidak ada yang boleh berdagang, jadi tidak ada
# nilai transaksi di sisi mana pun. Bukan error, dan bukan pangsa 0%.
ZERO_PANEL = panel_payload([("XL", 0, 0), ("DH", 0, 0)], [("DH", 0, 0)])


def write_corpus(tmp_path, dailies=(), panels=(), suspensions=()):
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
    add(concentration.BROKERS_PATH, concentration.BROKERS_PARAMS,
        {"results": list(BROKERS)})
    add(labels.SUSPENSIONS_PATH, labels.SUSPENSIONS_PARAMS,
        {"results": list(suspensions)})

    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def halted_corpus(tmp_path, suspensions=(HALT,), name="halt"):
    """Deret harian nol seluruhnya, panel broker nol seluruhnya."""
    return write_corpus(
        tmp_path / name,
        dailies=[("AAAA", {}, daily_rows("AAAA", DATES, [1000] * 10, [0] * 10))],
        panels=[("AAAA", {"n_brokers": 10}, ZERO_PANEL)],
        suspensions=list(suspensions))


def quiet_corpus(tmp_path, name="sepi"):
    """Kontrolnya: benar-benar diperdagangkan, hanya sedikit."""
    volumes = [1_000, 900, 1_100, 950, 1_050, 1_000, 980, 1_020, 990, 100]
    return write_corpus(
        tmp_path / name,
        dailies=[("AAAA", {}, daily_rows("AAAA", DATES, [1000] * 10, volumes))],
        panels=[("AAAA", {"n_brokers": 10}, LIVE_PANEL)],
        suspensions=[])


def thresholds_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": 9, "updated_on": "2026-09-09",
           "current": {"concentration": 0.45, "volume_anomaly": 5.0,
                       "momentum": 90.0, "catalyst": 0.10},
           "bounds": {}, "cohort_factors": {}, "history": []}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


class WatchedCache:
    """`Cache` yang mencatat tiap path yang diminta, dengan urutannya.

    Cara membuktikan pipeline benar-benar **mengecek** arsip suspensi, bukan
    kebetulan menghasilkan jawaban yang benar karena deret nol tidak pernah
    melewati ambang apa pun.
    """

    def __init__(self, source):
        self._source = source
        self.asked = []

    def __getattr__(self, name):
        return getattr(self._source, name)

    def get(self, path, params=None, method="GET"):
        self.asked.append(path)
        return self._source.get(path, params, method)


# --- 1. arsipnya benar-benar dibaca -----------------------------------------
def test_the_suspension_archive_is_read_before_a_flat_series_is_explained(tmp_path):
    """Jawaban yang benar tanpa mengecek arsip adalah kebetulan, bukan pemeriksaan."""
    source = WatchedCache(halted_corpus(tmp_path))
    result = profile.build("AAAA", cache=source, cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"),
                           as_of="2026-08-24")
    assert labels.SUSPENSIONS_PATH in source.asked
    assert result.suspended is True
    assert [e.date.isoformat() for e in result.suspension_events] == \
        [HALT["suspension_date"]]


def test_the_halt_is_named_by_its_reason_class(tmp_path):
    """Pembacanya diberi tahu halt yang mana, bukan sekadar bahwa ada halt."""
    result = profile.build("AAAA", cache=halted_corpus(tmp_path), cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert [e.reason_class for e in result.suspension_events] == ["cooling_down"]


def test_every_zero_axis_carries_the_announcement_that_explains_it(tmp_path):
    """Bukti melekat pada sumbu yang berlubang, bukan hanya pada ringkasannya."""
    corpus = halted_corpus(tmp_path)
    bars = thresholds_file(tmp_path / "bar")
    for result in (volume_anomaly.score("AAAA", cache=corpus, thresholds_path=bars),
                   momentum.score("AAAA", cache=corpus, thresholds_path=bars),
                   concentration.score("AAAA", cache=corpus, thresholds_path=bars)):
        assert result.all_zero is True
        assert [e.date.isoformat() for e in result.suspensions_in_window] == \
            [HALT["suspension_date"]]


# --- 2. profilnya menyebutnya, dan tidak menyimpulkan apa pun ----------------
def test_a_halted_stock_lights_no_axis(tmp_path):
    """Nol bukan pengukuran ekstrem. Tidak ada sumbu yang boleh menyala karenanya."""
    result = profile.build("AAAA", cache=halted_corpus(tmp_path), cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.axes_fired == 0
    assert result.fired_axes == ()
    for reading in result.readings:
        assert reading.state != profile.LIT
        assert reading.fired is not True


def test_a_zero_reading_is_unmeasured_not_a_zero_measurement(tmp_path):
    """`tidak_diketahui`, bukan `tidak_menyala`: tidak ada yang diukur di sini.

    Bedanya bukan kosmetik. `tidak_menyala` berarti sudah diukur dan hasilnya di
    bawah ambang — pernyataan tentang pasar. Untuk saham yang di-halt, pernyataan
    itu tidak pernah bisa dibuat.
    """
    result = profile.build("AAAA", cache=halted_corpus(tmp_path), cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    by_axis = {r.axis: r for r in result.readings}
    for axis in (volume_anomaly.AXIS, concentration.AXIS):
        assert by_axis[axis].state == profile.UNKNOWN
        assert by_axis[axis].value is None
        assert by_axis[axis].unknown_reason


def test_the_description_says_halted_and_never_says_quiet(tmp_path):
    """Kalimat yang dibaca orang: berhenti diperdagangkan, bukan tidak diminati."""
    text = profile.describe(
        profile.build("AAAA", cache=halted_corpus(tmp_path), cutoff=CUTOFF,
                      thresholds_path=thresholds_file(tmp_path / "bar")))
    assert "berhenti diperdagangkan" in text
    assert "suspensi di dalam jendela: 2026-08-11" in text
    # "sepi" hanya boleh muncul sebagai penyangkalan — deret nol berarti tidak ada
    # perdagangan, bukan tidak ada peminat.
    lowered = text.lower()
    for position in range(len(lowered)):
        position = lowered.find("sepi", position)
        if position < 0:
            break
        assert lowered[max(0, position - 6):position].strip().endswith("bukan"), (
            f"kata 'sepi' dipakai sebagai kesimpulan: ...{text[position - 40:position + 40]}...")


def test_without_an_announcement_the_cause_is_stated_as_unknown(tmp_path):
    """Arsip yang kosong bukan izin menyimpulkan sahamnya sepi.

    Deret nol tanpa pengumuman tetap deret nol. Yang berubah hanya sebabnya —
    belum diketahui — dan itu yang ditulis, bukan "tidak ada temuan".
    """
    result = profile.build("AAAA", cache=halted_corpus(tmp_path, suspensions=(),
                                                       name="tanpa-pengumuman"),
                           cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.suspended is True
    assert result.suspension_events == ()
    assert result.axes_fired == 0
    assert "belum diketahui" in profile.describe(result)


def test_a_zero_daily_series_alone_is_enough_to_call_it_halted(tmp_path):
    """Sisi lain dari audit yang sama: deret harian nol, panel brokernya utuh.

    Sebuah implementasi yang membaca deret nol sebagai "sepi" lolos dari tes
    kembar di bawah — panel brokernya masih menyelamatkannya — jadi kedua arah
    harus diuji terpisah.
    """
    corpus = write_corpus(
        tmp_path / "deret-nol",
        dailies=[("AAAA", {}, daily_rows("AAAA", DATES, [1000] * 10, [0] * 10))],
        panels=[("AAAA", {"n_brokers": 10}, LIVE_PANEL)],
        suspensions=[HALT])
    result = profile.build("AAAA", cache=corpus, cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.suspended is True
    assert [e.date.isoformat() for e in result.suspension_events] == \
        [HALT["suspension_date"]]


def test_a_zero_broker_panel_alone_is_enough_to_call_it_halted(tmp_path):
    """Auditnya menyeluruh: panel nol pun lubang data, meski deret hariannya utuh."""
    corpus = write_corpus(
        tmp_path / "panel-nol",
        dailies=[("AAAA", {},
                  daily_rows("AAAA", DATES, [1000] * 10, [1_000] * 9 + [50_000]))],
        panels=[("AAAA", {"n_brokers": 10}, ZERO_PANEL)],
        suspensions=[HALT])
    result = profile.build("AAAA", cache=corpus, cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.suspended is True
    assert result.suspension_events


# --- 3. kontrol: yang sepi tidak ikut disebut halt ---------------------------
def test_a_thinly_traded_stock_is_not_called_halted(tmp_path):
    """Penjaga yang menyebut semua deret datar sebagai halt tidak menjaga apa pun."""
    corpus = quiet_corpus(tmp_path)
    bars = thresholds_file(tmp_path / "bar")
    result = profile.build("AAAA", cache=corpus, cutoff=CUTOFF, thresholds_path=bars)
    assert result.suspended is False
    assert result.suspension_events == ()

    volume = volume_anomaly.score("AAAA", cache=corpus, thresholds_path=bars)
    assert volume.all_zero is False
    assert volume.status == "quiet"
    assert volume.ratio is not None


def test_a_stock_with_zero_volume_on_some_days_is_not_halted(tmp_path):
    """Sebagian nol adalah hari tanpa transaksi. Seluruhnya nol adalah halt."""
    volumes = [1_000, 0, 1_100, 0, 1_050, 1_000, 0, 1_020, 990, 900]
    corpus = write_corpus(
        tmp_path / "sebagian",
        dailies=[("AAAA", {}, daily_rows("AAAA", DATES, [1000] * 10, volumes))],
        panels=[("AAAA", {"n_brokers": 10}, LIVE_PANEL)],
        suspensions=[])
    result = profile.build("AAAA", cache=corpus, cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.suspended is False
    volume = volume_anomaly.score("AAAA", cache=corpus,
                                  thresholds_path=thresholds_file(tmp_path / "bar"))
    assert volume.n_zero == 3
    assert volume.all_zero is False


# --- 4. tidak pernah menjadi peringatan --------------------------------------
def test_a_halted_stock_never_becomes_a_warning(tmp_path):
    """Ujung pipeline: baris yang masuk matriks, bukan hanya profil di layar."""
    corpus = halted_corpus(tmp_path)
    calls = evaluate.contenders(CUTOFF, ["AAAA"], cache=corpus,
                                thresholds_path=thresholds_file(tmp_path / "bar"))
    ours = calls[evaluate.SYSTEM]
    assert [c.symbol for c in ours] == ["AAAA"]
    assert ours[0].warned is False
    assert "0/4 menyala" in ours[0].detail


def test_the_same_pipeline_can_still_warn_on_a_stock_that_trades(tmp_path):
    """Kontrol ujung pipeline: penilaian yang tidak pernah memperingatkan apa pun
    juga lulus tes di atas, dan tidak membuktikan apa-apa."""
    volumes = [1_000] * 9 + [500_000]
    closes = [100, 110, 121, 133, 146, 161, 177, 195, 214, 236]
    corpus = write_corpus(
        tmp_path / "ramai",
        dailies=[("AAAA", {}, daily_rows("AAAA", DATES, closes, volumes))],
        panels=[("AAAA", {"n_brokers": 10}, LIVE_PANEL)],
        suspensions=[])
    calls = evaluate.contenders(CUTOFF, ["AAAA"], cache=corpus, min_axes=1,
                                thresholds_path=thresholds_file(tmp_path / "bar"))
    assert calls[evaluate.SYSTEM][0].warned is True


# --- aturan turunan §7: bukti, bukan fitur -----------------------------------
def test_the_in_window_announcement_is_evidence_and_never_a_feature(tmp_path):
    """Pengumuman di dalam jendela menjelaskan lubangnya; ia tidak boleh jadi fitur.

    Sumbu riwayat dipanggil dengan cutoff = hari pertama jendela, jadi halt
    2026-08-11 tidak terhitung sebagai riwayat pada jendela yang sama. Yang
    terhitung hanya halt 2025 — yang memang sudah diketahui pembaca saat itu.
    """
    corpus = halted_corpus(tmp_path, suspensions=(OLD_HALT, HALT), name="dua-halt")
    result = profile.build("AAAA", cache=corpus, cutoff=CUTOFF,
                           thresholds_path=thresholds_file(tmp_path / "bar"))
    riwayat = next(r for r in result.supporting if r.axis == "history")
    assert riwayat.value == 1                      # hanya yang 2025
    assert [e.date.isoformat() for e in result.suspension_events] == \
        [HALT["suspension_date"]]
    assert result.axes_fired == 0
