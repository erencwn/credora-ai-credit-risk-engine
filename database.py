"""
Credora - MLOps Veri Kayıt Katmanı
====================================
Kullanıcı "MLOps Aktif" onayını verdiğinde, başvuru sırasında modele giden
özellikler + üretilen tahmin sonucu, ileride modeli yeniden eğitmek
(retraining) ve model performansını izlemek (drift detection) için
buraya kaydedilir.

Kişisel veri (isim, TC kimlik, telefon vb.) formda zaten toplanmıyor,
sadece finansal/demografik özellikler kaydediliyor.
"""

import sqlite3
import json
from datetime import datetime, timezone
from contextlib import contextmanager

DB_PATH = "credora.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Uygulama ayağa kalkarken bir kere çağrılır. Tablo yoksa oluşturur."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS basvurular (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                olusturma_zamani TEXT NOT NULL,

                -- Ham girdi verileri (modelin gördüğü özellikler)
                yas REAL,
                egitim_seviyesi TEXT,
                calisma_durumu TEXT,
                deneyim_yil REAL,
                aylik_gelir REAL,
                aylik_borc REAL,
                toplam_varlik REAL,
                kredi_gecmisi REAL,
                kredi_tutari REAL,
                vade INTEGER,
                kredi_puani REAL,
                para_birimi TEXT,

                -- Türetilmiş / modele giden değerler
                tahmini_yillik_faiz REAL,
                aylik_taksit REAL,
                borc_gelir_orani REAL,

                -- Model çıktısı
                onay_olasiligi REAL,
                sonuc TEXT,              -- 'ONAY' / 'RED'
                model_versiyonu TEXT,

                -- Ham girdi JSON olarak da saklanır (ileride şema değişirse geri dönebilmek için)
                ham_veri_json TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_basvurular_zaman
            ON basvurular(olusturma_zamani)
        """)


def basvuru_kaydet(girdi: dict, tahmin: dict, model_versiyonu: str = "lr_v1"):
    """
    girdi: kullanıcıdan gelen request.json (payload)
    tahmin: {"onay_olasiligi": float, "sonuc": "ONAY"/"RED",
             "tahmini_yillik_faiz": float, "aylik_taksit": float,
             "borc_gelir_orani": float}
    """
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO basvurular (
                olusturma_zamani, yas, egitim_seviyesi, calisma_durumu,
                deneyim_yil, aylik_gelir, aylik_borc, toplam_varlik,
                kredi_gecmisi, kredi_tutari, vade, kredi_puani, para_birimi,
                tahmini_yillik_faiz, aylik_taksit, borc_gelir_orani,
                onay_olasiligi, sonuc, model_versiyonu, ham_veri_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            girdi.get("yas"),
            girdi.get("egitim_seviyesi"),
            girdi.get("calisma_durumu"),
            girdi.get("deneyim_yil"),
            girdi.get("aylik_gelir"),
            girdi.get("aylik_borc"),
            girdi.get("toplam_varlik"),
            girdi.get("kredi_gecmisi"),
            girdi.get("kredi_tutari"),
            girdi.get("vade"),
            girdi.get("kredi_puani"),
            girdi.get("para_birimi"),
            tahmin.get("tahmini_yillik_faiz"),
            tahmin.get("aylik_taksit"),
            tahmin.get("borc_gelir_orani"),
            tahmin.get("onay_olasiligi"),
            tahmin.get("sonuc"),
            model_versiyonu,
            json.dumps(girdi, ensure_ascii=False),
        ))


def basvuru_sayisi() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM basvurular").fetchone()["c"]
