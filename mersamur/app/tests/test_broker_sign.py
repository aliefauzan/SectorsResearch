"""Pertanyaan juri #2: apakah tanda dominansi brokernya benar?

Supertype menulis peringatannya sendiri di resep GNN mereka, dan
`research/docs/api/10-domain-pitfalls.md` §1 mengutipnya: kesalahan paling umum
pada endpoint ini adalah menjumlahkan **seluruh** net sisi beli dengan seluruh net
sisi jual. Pasar ekuitas zero-sum — tiap pembeli punya penjual — jadi hasilnya
mendekati nol untuk emiten apa pun, sinyalnya terlihat datar, dan pembacanya
menyimpulkan tidak ada apa-apa.

Bentuk yang benar adalah **dominansi**: akumulator terbesar melawan distributor
terbesar.

    # SALAH — selalu mendarat dekat nol, pasar zero-sum
    total = sum(b["net_idr"] for b in buyers) + sum(s["net_idr"] for s in sellers)

    # BENAR — `net_idr` sudah negatif di sisi jual, jadi ini MENJUMLAHKAN
    dominance = buyers[0]["net_idr"] + sellers[0]["net_idr"]

Ada dua jebakan bersarang, dan berkas ini menargetkan keduanya:

  * **cakupannya** — hanya baris pertama tiap sisi, bukan seluruh sisi;
  * **tandanya** — `net_idr` sisi jual sudah negatif, jadi rumusnya menambah di
    tempat intuisi menyuruh mengurangi. Salah di sini membalik seluruh sumbu, dan
    membaliknya tanpa suara: angkanya tetap masuk akal, artinya berlawanan.

Yang membuat tes ini bukan tautologi: rumus yang salah dijalankan berdampingan
dengan rumus produk atas **panel yang benar-benar direkam dari API**, dan pada
BBCA keduanya tidak sekadar berbeda besarnya — tandanya berlawanan. Yang satu
bilang akumulasi, yang lain bilang distribusi.

Nol kredit: seluruh berkas ini membaca `research/harness/recorded/` atau direktori
sementara. Tidak ada socket yang dibuka.
"""
import json

from app import profile
from app import cache as cache_mod
from app.axes import concentration
from app.cache import Cache

# Panel broker yang sudah dibayar dan ada di repo. Simbolnya, bukan berkasnya,
# supaya tes menempuh jalur pencarian produk (`Cache` + `_manifest.json`).
RECORDED = ("LIFE", "ASLI", "NICK", "TRUK", "PPGL", "SAFE", "PACK", "CSMI",
            "TMPO", "AGAR", "BBCA", "BBRI", "TLKM", "ADRO")


# --- rumus-rumus yang dibandingkan ------------------------------------------
def dominance(payload):
    """Bentuk yang benar, ditulis ulang di sini supaya tesnya bukan tautologi."""
    buyers = payload.get("top_buyers") or []
    sellers = payload.get("top_sellers") or []
    return ((buyers[0]["net_idr"] if buyers else 0)
            + (sellers[0]["net_idr"] if sellers else 0))


def both_sides_in_full(payload):
    """Kesalahan yang dikutip §1: seluruh sisi beli ditambah seluruh sisi jual."""
    return (sum(b["net_idr"] for b in payload.get("top_buyers") or [])
            + sum(s["net_idr"] for s in payload.get("top_sellers") or []))


def subtracting_the_seller(payload):
    """Kesalahan tanda: mengurangi net penjual yang memang sudah negatif."""
    buyers = payload.get("top_buyers") or []
    sellers = payload.get("top_sellers") or []
    return ((buyers[0]["net_idr"] if buyers else 0)
            - (sellers[0]["net_idr"] if sellers else 0))


# --- korpus buatan -----------------------------------------------------------
def rows(side, triples):
    """`(kode, buy_idr, sell_idr)` menjadi baris API, berperingkat.

    `net_idr` dihitung di sini seperti API menghitungnya — beli dikurangi jual —
    sehingga sisi jual keluar negatif dengan sendirinya, bukan karena tes
    memaksakannya.
    """
    out = [{"rank": i + 1, "broker_code": code, "buy_idr": buy, "sell_idr": sell,
            "net_idr": buy - sell} for i, (code, buy, sell) in enumerate(triples)]
    return {side: out}


def write_panel(tmp_path, payload, symbol="AAAA", brokers=()):
    """Satu panel broker plus daftar broker, ditulis seperti `capture.py`."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = {}

    def add(path, params, body):
        key = cache_mod.slug(path, params)
        (tmp_path / f"{key}.json").write_text(json.dumps(body), encoding="utf-8")
        manifest[key] = {"path": path, "params": params, "status": 200,
                         "est_cost": 1, "fetched_at": 0, "cost_headers": {}}

    add(concentration.BROKER_SUMMARY_PATH.format(symbol=symbol),
        {"n_brokers": 10}, payload)
    add(concentration.BROKERS_PATH, concentration.BROKERS_PARAMS,
        {"results": list(brokers)})
    (tmp_path / "_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Cache(root=str(tmp_path))


def thresholds_file(tmp_path, bar=0.45):
    tmp_path.mkdir(parents=True, exist_ok=True)
    doc = {"version": 9, "updated_on": "2026-09-09",
           "current": {"concentration": bar}, "bounds": {}, "cohort_factors": {},
           "history": []}
    path = tmp_path / "thresholds.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def balanced_panel():
    """Panel zero-sum sempurna: tiap rupiah yang dibeli seseorang, dijual orang lain.

    Ini bentuk paling jujur dari jebakannya. Jumlah kedua sisi persis nol, sedangkan
    yang sebenarnya terjadi adalah satu broker mengakumulasi 900 juta melawan
    distributor terbesar yang melepas 400 juta.
    """
    buyers = [("XL", 1_000_000_000, 100_000_000),     # net +900 juta
              ("AT", 300_000_000, 100_000_000),       # net +200 juta
              ("CC", 200_000_000, 100_000_000)]       # net +100 juta
    sellers = [("DH", 100_000_000, 500_000_000),      # net -400 juta
               ("YP", 100_000_000, 500_000_000),      # net -400 juta
               ("PD", 100_000_000, 500_000_000)]      # net -400 juta
    payload = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09"}
    payload.update(rows("top_buyers", buyers))
    payload.update(rows("top_sellers", sellers))
    return payload


# --- cakupan: baris pertama, bukan seluruh sisi ------------------------------
def test_the_axis_adds_the_two_extremes_on_every_recorded_panel():
    """Kontraknya, diuji atas 14 panel nyata sekaligus.

    Bukan satu contoh yang dipilih: tiap panel yang pernah dibeli harus memenuhi
    `dominansi == top_buyers[0].net_idr + top_sellers[0].net_idr` persis.
    """
    source = Cache()
    for symbol in RECORDED:
        payload = concentration.panel(symbol, cache=source)
        result = concentration.score(symbol, cache=source)
        assert result.net_dominance == dominance(payload), symbol


def test_summing_both_sides_in_full_collapses_on_a_zero_sum_panel(tmp_path):
    """Jebakannya, direproduksi: rumus salah mendarat nol saat panelnya ramai."""
    payload = balanced_panel()
    assert both_sides_in_full(payload) == 0

    corpus = write_panel(tmp_path / "seimbang", payload)
    result = concentration.score("AAAA", cache=corpus,
                                 thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.net_dominance == 500_000_000
    assert result.net_dominance != both_sides_in_full(payload)
    # Dan panelnya jelas tidak sepi: setengah miliar bergerak di tiap sisi.
    assert result.panel_value_idr > 2_000_000_000


def test_only_the_first_row_of_each_side_counts(tmp_path):
    """Baris 2 dan seterusnya boleh berubah sekeras apa pun; dominansi tidak bergeser.

    Ini yang menggagalkan implementasi mana pun yang menjumlahkan seluruh sisi,
    tanpa perlu membaca kodenya: hasilnya di sini akan bergerak, dan seharusnya
    tidak.
    """
    bars = thresholds_file(tmp_path / "bar")
    base = balanced_panel()
    louder = json.loads(json.dumps(base))
    for row in louder["top_buyers"][1:]:
        row["buy_idr"] += 50_000_000_000
        row["net_idr"] = row["buy_idr"] - row["sell_idr"]
    for row in louder["top_sellers"][1:]:
        row["sell_idr"] += 90_000_000_000
        row["net_idr"] = row["buy_idr"] - row["sell_idr"]

    first = concentration.score("AAAA", cache=write_panel(tmp_path / "a", base),
                                thresholds_path=bars)
    second = concentration.score("AAAA", cache=write_panel(tmp_path / "b", louder),
                                 thresholds_path=bars)
    assert first.net_dominance == second.net_dominance == 500_000_000
    # Rumus yang salah bergeser 80 miliar untuk perubahan yang sama — dan pada
    # panel dasarnya ia bernilai nol, yang persis keluhan §1.
    assert both_sides_in_full(base) == 0
    assert both_sides_in_full(louder) - both_sides_in_full(base) == -80_000_000_000


def test_the_wrong_formula_disagrees_in_sign_on_recorded_panels():
    """Bukan sekadar beda besar — beda arah, pada data yang benar-benar dibeli.

    BBCA adalah kasus yang paling telak: menjumlahkan seluruh dua sisi menghasilkan
    angka **positif** (terbaca akumulasi) sementara akumulator terbesar sebenarnya
    kalah dari distributor terbesar. Produk yang memakai rumus salah akan
    menceritakan kebalikan dari apa yang terjadi di tape.
    """
    source = Cache()
    payload = concentration.panel("BBCA", cache=source)
    assert both_sides_in_full(payload) > 0
    assert dominance(payload) < 0
    assert concentration.score("BBCA", cache=source).net_dominance < 0
    assert concentration.score("BBCA", cache=source).accumulating is False

    disagree = [s for s in RECORDED
                if (both_sides_in_full(concentration.panel(s, cache=source)) > 0)
                != (dominance(concentration.panel(s, cache=source)) > 0)]
    assert len(disagree) >= 3, (
        f"hanya {disagree} yang berbeda tanda; ekspektasinya beberapa panel")


# --- tanda: menambah, bukan mengurangi ---------------------------------------
def test_sellers_net_is_already_negative_in_every_recorded_panel():
    """Alasan rumusnya menambah, dibaca dari API dan bukan dari dokumentasi."""
    source = Cache()
    for symbol in RECORDED:
        sellers = concentration.panel(symbol, cache=source).get("top_sellers") or []
        assert sellers, symbol
        assert all(row["net_idr"] <= 0 for row in sellers), symbol


def test_subtracting_the_seller_inverts_a_distribution_led_panel(tmp_path):
    """Panel yang dipimpin distribusi harus terbaca negatif. Mengurangi membaliknya."""
    buyers = [("XL", 200_000_000, 50_000_000)]        # net +150 juta
    sellers = [("DH", 50_000_000, 900_000_000)]       # net -850 juta
    payload = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09"}
    payload.update(rows("top_buyers", buyers))
    payload.update(rows("top_sellers", sellers))

    result = concentration.score("AAAA", cache=write_panel(tmp_path / "dist", payload),
                                 thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.net_dominance == -700_000_000
    assert result.accumulating is False
    # Rumus yang mengurangi memberi +1 miliar untuk panel yang sama: arah terbalik,
    # angkanya tetap terlihat masuk akal, dan tidak ada yang meledak.
    assert subtracting_the_seller(payload) == 1_000_000_000
    assert (subtracting_the_seller(payload) > 0) != (result.net_dominance > 0)


def test_an_accumulation_led_panel_reads_positive(tmp_path):
    """Kontrol arah yang lain: tanda tidak dipaku negatif, ia mengikuti panelnya."""
    buyers = [("XL", 900_000_000, 50_000_000)]        # net +850 juta
    sellers = [("DH", 50_000_000, 200_000_000)]       # net -150 juta
    payload = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09"}
    payload.update(rows("top_buyers", buyers))
    payload.update(rows("top_sellers", sellers))

    result = concentration.score("AAAA", cache=write_panel(tmp_path / "akum", payload),
                                 thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.net_dominance == 700_000_000
    assert result.accumulating is True


def test_dominance_is_not_the_concentration_ratio(tmp_path):
    """Dua pengukuran, dua pertanyaan.

    Sisi beli boleh sangat terpusat sementara dominansinya negatif: satu broker
    memborong seluruh sisi beli dan tetap kalah oleh distributor terbesar. Menukar
    keduanya adalah cara lain membalik cerita.
    """
    buyers = [("XL", 1_000_000_000, 0)]               # 100% sisi beli, net +1 miliar
    sellers = [("DH", 0, 3_000_000_000)]              # net -3 miliar
    payload = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09"}
    payload.update(rows("top_buyers", buyers))
    payload.update(rows("top_sellers", sellers))

    result = concentration.score("AAAA", cache=write_panel(tmp_path / "campur", payload),
                                 thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.top1_ratio == 1.0
    assert result.net_dominance == -2_000_000_000
    assert result.accumulating is False


# --- tanda yang sampai ke layar ----------------------------------------------
def test_the_sign_survives_into_the_profile_a_reader_sees():
    """Tanda yang benar di dalam sumbu tidak berguna kalau dibalik saat ditampilkan."""
    source = Cache()
    payload = concentration.panel("BBCA", cache=source)
    result = profile.build("BBCA", cache=source)
    context = {name: value for name, value, _unit, _src
               in next(r for r in result.readings
                       if r.axis == concentration.AXIS).context}
    assert context["dominansi_neto_idr"] == dominance(payload)
    assert context["dominansi_neto_idr"] < 0


def test_the_description_states_the_direction_without_a_verdict():
    """Deskriptif: arah akumulasi/distribusi boleh disebut, anjuran tidak."""
    text = concentration.describe(concentration.score("BBCA", cache=Cache()))
    lowered = text.lower()
    assert "dominansi" in lowered
    for word in ("beli", "jual", "rekomendasi", "target", "sinyal", "cuan"):
        assert f" {word} " not in f" {lowered} ", word


def test_a_panel_with_one_empty_side_does_not_crash_or_invent_a_number(tmp_path):
    """Sisi jual kosong berarti tidak ada distributor, bukan distributor bernilai nol.

    Dominansinya lalu hanya net pembeli terbesar — dan yang penting: rumusnya tidak
    boleh melempar IndexError, karena panel pendek memang ada di IDX (NICK punya
    lima pembeli).
    """
    payload = {"symbol": "AAAA.JK", "start": "2026-06-11", "end": "2026-09-09"}
    payload.update(rows("top_buyers", [("XL", 500_000_000, 100_000_000)]))
    payload["top_sellers"] = []

    result = concentration.score("AAAA", cache=write_panel(tmp_path / "sepi", payload),
                                 thresholds_path=thresholds_file(tmp_path / "bar"))
    assert result.net_dominance == 400_000_000
    assert result.n_sellers == 0
    assert result.thin_book is True
