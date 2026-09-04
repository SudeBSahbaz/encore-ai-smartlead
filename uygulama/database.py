import sqlite3
from contextlib import closing
from pathlib import Path

from flask import current_app


def baglanti_al():
    yol = current_app.config["DATABASE_URL"]
    if yol != ":memory:":
        Path(yol).parent.mkdir(parents=True, exist_ok=True)
    baglanti = sqlite3.connect(yol)
    baglanti.row_factory = sqlite3.Row
    return baglanti


def veritabani_baslat(uygulama):
    with uygulama.app_context(), closing(baglanti_al()) as baglanti:
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS asistan_etkilesimleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oturum_kodu TEXT NOT NULL,
                kullanici_mesaji TEXT NOT NULL CHECK(length(kullanici_mesaji) BETWEEN 1 AND 1200),
                asistan_yaniti TEXT,
                saglayici TEXT NOT NULL,
                basarili INTEGER NOT NULL DEFAULT 1 CHECK(basarili IN (0, 1)),
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS musteri_adaylari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL CHECK(length(isim) BETWEEN 2 AND 100),
                telefon TEXT NOT NULL CHECK(length(telefon) BETWEEN 10 AND 20),
                mesaj TEXT CHECK(length(mesaj) <= 1000),
                etkilesim_id INTEGER,
                iletisim_izni INTEGER NOT NULL DEFAULT 0 CHECK(iletisim_izni IN (0, 1)),
                durum TEXT NOT NULL DEFAULT 'uyelik_daveti_gosterildi',
                sohbet_ozeti TEXT,
                sohbet_gecmisi TEXT,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (etkilesim_id) REFERENCES asistan_etkilesimleri(id)
            )
        """)
        mevcut_kolonlar = {satir[1] for satir in baglanti.execute("PRAGMA table_info(musteri_adaylari)")}
        if "sohbet_ozeti" not in mevcut_kolonlar:
            baglanti.execute("ALTER TABLE musteri_adaylari ADD COLUMN sohbet_ozeti TEXT")
        if "sohbet_gecmisi" not in mevcut_kolonlar:
            baglanti.execute("ALTER TABLE musteri_adaylari ADD COLUMN sohbet_gecmisi TEXT")
        baglanti.commit()


def asistan_etkilesimi_ekle(oturum_kodu, kullanici_mesaji, asistan_yaniti, saglayici, basarili=True):
    with closing(baglanti_al()) as baglanti:
        imlec = baglanti.execute(
            "INSERT INTO asistan_etkilesimleri "
            "(oturum_kodu, kullanici_mesaji, asistan_yaniti, saglayici, basarili) VALUES (?, ?, ?, ?, ?)",
            (oturum_kodu, kullanici_mesaji, asistan_yaniti, saglayici, int(basarili)),
        )
        baglanti.commit()
        return imlec.lastrowid


def tum_etkilesimleri_getir():
    with closing(baglanti_al()) as baglanti:
        satirlar = baglanti.execute(
            "SELECT id, oturum_kodu, kullanici_mesaji, asistan_yaniti, saglayici, "
            "basarili, olusturulma_tarihi FROM asistan_etkilesimleri "
            "ORDER BY datetime(olusturulma_tarihi) DESC, id DESC"
        ).fetchall()
    return [dict(s) for s in satirlar]


def etkilesim_oturuma_ait_mi(kimlik, oturum_kodu):
    with closing(baglanti_al()) as baglanti:
        satir = baglanti.execute(
            "SELECT 1 FROM asistan_etkilesimleri WHERE id = ? AND oturum_kodu = ? AND basarili = 1",
            (kimlik, oturum_kodu),
        ).fetchone()
    return satir is not None


def etkilesim_sil(kimlik):
    with closing(baglanti_al()) as baglanti:
        imlec = baglanti.execute("DELETE FROM asistan_etkilesimleri WHERE id = ?", (kimlik,))
        baglanti.commit()
        return imlec.rowcount > 0


def musteri_adayi_ekle(isim, telefon, mesaj, etkilesim_id, iletisim_izni, sohbet_ozeti=None, sohbet_gecmisi=None):
    with closing(baglanti_al()) as baglanti:
        imlec = baglanti.execute(
            "INSERT INTO musteri_adaylari "
            "(isim, telefon, mesaj, etkilesim_id, iletisim_izni, sohbet_ozeti, sohbet_gecmisi) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (isim, telefon, mesaj or None, etkilesim_id, int(iletisim_izni), sohbet_ozeti, sohbet_gecmisi),
        )
        baglanti.commit()
        return imlec.lastrowid


def tum_adaylari_getir():
    with closing(baglanti_al()) as baglanti:
        satirlar = baglanti.execute("""
            SELECT a.id, a.isim, a.telefon, a.mesaj, a.etkilesim_id,
                   a.iletisim_izni, a.durum, a.sohbet_ozeti, a.sohbet_gecmisi,
                   a.olusturulma_tarihi,
                   e.oturum_kodu, e.kullanici_mesaji, e.asistan_yaniti
            FROM musteri_adaylari AS a
            LEFT JOIN asistan_etkilesimleri AS e ON e.id = a.etkilesim_id
            ORDER BY datetime(a.olusturulma_tarihi) DESC, a.id DESC
        """).fetchall()
    return [dict(s) for s in satirlar]


def musteri_adayi_sil(kimlik):
    with closing(baglanti_al()) as baglanti:
        imlec = baglanti.execute("DELETE FROM musteri_adaylari WHERE id = ?", (kimlik,))
        baglanti.commit()
        return imlec.rowcount > 0
