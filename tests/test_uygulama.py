import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uygulama import uygulama_olustur
from uygulama.servisler.yapay_zeka_servisi import yapay_zeka_servisi


class EncoreTestleri(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory()
        db = str(Path(self.gecici.name) / "test.db")
        self.app = uygulama_olustur("test", {"DATABASE_URL": db, "PANEL_PASSWORD": "test123", "SECRET_KEY": "test"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.gecici.cleanup()

    def test_saglik(self):
        cevap = self.client.get("/saglik-durumu")
        self.assertEqual(cevap.status_code, 200)
        self.assertEqual(cevap.json["durum"], "çalışıyor")

    def test_bos_sohbet_reddedilir(self):
        cevap = self.client.post("/api/sohbet", json={"mesaj": ""})
        self.assertEqual(cevap.status_code, 400)

    def test_groq_gpt_oss_yeterli_yanit_butcesi_kullanir(self):
        with patch("uygulama.servisler.yapay_zeka_servisi.requests.post") as istek:
            istek.return_value.json.return_value = {
                "choices": [{"message": {"content": "İstanbul için plan hazırlayalım."}}]
            }
            with self.app.app_context():
                yanit = yapay_zeka_servisi._openai_uyumlu_cagir(
                    "https://api.groq.com/openai/v1/chat/completions",
                    "gsk_test", "openai/gpt-oss-20b", "Tiyatro istiyorum", [],
                )
            govde = istek.call_args.kwargs["json"]
            self.assertEqual(yanit, "İstanbul için plan hazırlayalım.")
            self.assertEqual(govde["reasoning_effort"], "low")
            self.assertEqual(govde["max_completion_tokens"], 1024)
            sistem = govde["messages"][0]["content"]
            self.assertIn("kesin uygun gün veya tarih ve saat aralığı", sistem)
            self.assertIn("Kullanıcı söylemeden belirli bir gün", sistem)
            self.assertIn("Hangi gün veya günlerde", sistem)
            self.assertIn("Markdown tablosu", sistem)
            self.assertIn("canlı veya doğrulanmış etkinlik veri kaynağı bağlı DEĞİLDİR", sistem)

    def test_yapay_zeka_markdown_yanitini_duz_metne_cevirir(self):
        ham = "## Plan\n| Gün | Etkinlik |\n|---|---|\n| Cumartesi | Tiyatro |\n\n**Toplam:** 900 TL"
        temiz = yapay_zeka_servisi._yaniti_temizle(ham)
        self.assertEqual(temiz, "Plan\nGün - Etkinlik\nCumartesi - Tiyatro\n\nToplam: 900 TL")
        self.assertNotIn("**", temiz)
        self.assertNotIn("|", temiz)

    def test_sohbet_kaydedilir(self):
        cevap = self.client.post("/api/sohbet", json={"mesaj": "Bu hafta sonu bir konser arıyorum"})
        self.assertEqual(cevap.status_code, 200)
        self.assertTrue(cevap.json["basari"])
        self.assertIn("etkilesim_id", cevap.json)
        self.client.post("/panel-giris", data={"sifre": "test123"})
        liste = self.client.get("/api/etkilesimler")
        self.assertEqual(liste.status_code, 200)
        self.assertEqual(liste.json["toplam"], 1)
        self.assertEqual(liste.json["etkilesimler"][0]["kullanici_mesaji"], "Bu hafta sonu bir konser arıyorum")

    def test_etkilesim_listesi_yetki_ister(self):
        self.assertEqual(self.client.get("/api/etkilesimler").status_code, 401)

    def test_ingilizce_api_sozlesmesi(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        chat = self.client.post("/api/chat", json={"message": "Bana tiyatro planı yap", "history": []})
        self.assertEqual(chat.status_code, 200)
        self.assertTrue(chat.json["success"])
        listed = self.client.get("/api/interactions")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json["count"], 1)
        self.assertEqual(listed.json["interactions"][0]["user_message"], "Bana tiyatro planı yap")
        lead = self.client.post("/api/leads", json={
            "name": "Deniz Kaya", "phone": "+90 555 222 33 44", "message": "Tiyatro planı",
            "interaction_id": chat.json["interaction_id"], "consent": True,
            "history": [{"role":"user", "content":"Bana tiyatro planı yap"}, {"role":"assistant", "content":chat.json["reply"]}],
        })
        self.assertEqual(lead.status_code, 201)
        self.assertTrue(lead.json["membership_invitation"])
        leads = self.client.get("/api/leads")
        self.assertEqual(leads.json["count"], 1)

    def test_uretim_etkilesim_listesi_api_anahtari_ister(self):
        app = uygulama_olustur("test", {
            "DATABASE_URL": str(Path(self.gecici.name) / "secure.db"),
            "REQUIRE_ADMIN_API_AUTH": True,
            "ADMIN_API_KEY": "gizli-test-anahtari",
        })
        client = app.test_client()
        self.assertEqual(client.get("/api/interactions").status_code, 401)
        cevap = client.get("/api/interactions", headers={"X-Admin-Key": "gizli-test-anahtari"})
        self.assertEqual(cevap.status_code, 200)

    def test_plan_kaydet_formu_sohbete_entegre(self):
        metin = self.client.get("/").get_data(as_text=True)
        self.assertIn('href="#etkinlikler">Etkinlikleri Keşfet</a>', metin)
        self.assertNotIn("Nasıl Çalışıyor?", metin)
        self.assertIn("Planını kaybetme", metin)
        self.assertIn('id="planSaveForm"', metin)
        self.assertIn('name="telefon"', metin)
        self.assertIn("Planlarını profilinde saklamak ve yönetmek ister misin?", metin)
        self.assertIn('href="/profile"', metin)
        self.assertIn('id="membershipInvite" hidden', metin)
        self.assertNotIn('id="membershipModal"', metin)
        self.assertNotIn("Demo Talep Et", metin)
        self.assertNotIn('id="adayForm"', metin)

    def test_plan_kaydi_panele_duser(self):
        sohbet = self.client.post("/api/sohbet", json={"mesaj": "1500 TL bütçeyle plan yap"})
        kayit = self.client.post("/api/adaylar", json={
            "isim": "Ayşe Yılmaz", "telefon": "+90 555 111 22 33",
            "mesaj": "1500 TL bütçeyle plan yap", "etkilesim_id": sohbet.json["etkilesim_id"],
            "iletisim_izni": True,
            "gecmis": [
                {"role":"user", "content":"Bu hafta sonu etkinlik arıyorum."},
                {"role":"assistant", "content":"Hangi bölgede olsun?"},
                {"role":"user", "content":"Kadıköy'de olsun."},
                {"role":"assistant", "content":"Bütçen nedir?"},
                {"role":"user", "content":"1500 TL bütçeyle plan yap"},
                {"role":"assistant", "content":sohbet.json["cevap"]},
            ],
        })
        self.assertEqual(kayit.status_code, 201)
        self.assertTrue(kayit.json["uyelik_daveti"])
        self.client.post("/panel-giris", data={"sifre": "test123"})
        metin = self.client.get("/panel").get_data(as_text=True)
        self.assertIn("Potansiyel Müşteriler", metin)
        self.assertIn("Dönüşüm Oranı", metin)
        self.assertIn("Ayşe Yılmaz", metin)
        self.assertIn("+905551112233", metin)
        self.assertIn("1500 TL bütçeyle plan yap", metin)
        self.assertIn("Bu hafta sonu etkinlik arıyorum.", metin)
        self.assertIn("Kadıköy&#39;de olsun.", metin)
        self.assertIn("Tüm konuşmayı görüntüle", metin)

    def test_plansiz_ve_izinsiz_lead_reddedilir(self):
        cevap = self.client.post("/api/adaylar", json={"isim": "Ali", "telefon": "05551112233", "iletisim_izni": False})
        self.assertEqual(cevap.status_code, 400)
        self.assertIn("iletisim_izni", cevap.json["alanlar"])
        self.assertIn("etkilesim_id", cevap.json["alanlar"])
        self.assertIn("gecmis", cevap.json["alanlar"])

    def test_gelistirme_sayfalari(self):
        for adres in ["/dashboard", "/profile", "/boxoffice", "/tickets", "/settings"]:
            with self.subTest(adres=adres):
                cevap = self.client.get(adres)
                self.assertEqual(cevap.status_code, 200)
                self.assertIn("Geliştirme aşamasındadır", cevap.get_data(as_text=True))

    def test_etkinlik_vitrini_ve_gise_etkilesimi(self):
        ana_sayfa = self.client.get("/").get_data(as_text=True)
        javascript_cevabi = self.client.get("/statik/app.js")
        javascript = javascript_cevabi.get_data(as_text=True)
        javascript_cevabi.close()
        self.assertIn('id="eventsTrack"', ana_sayfa)
        self.assertEqual(ana_sayfa.count("🎟"), 6)
        self.assertIn("encoreGise", javascript)
        self.assertIn("otomatikKaydirmaDuraklatildi", javascript)
        self.assertIn("Bilet gişede", javascript)

    def test_profil_ve_sekmeli_ayarlar(self):
        profil = self.client.get("/profile").get_data(as_text=True)
        ayarlar = self.client.get("/settings").get_data(as_text=True)
        self.assertIn("Üyelik bilgilerin", profil)
        self.assertIn(">Üye Ol</button>", profil)
        self.assertIn('data-settings-tab="plan"', ayarlar)
        self.assertIn('data-settings-pane="password"', ayarlar)

    def test_tum_sayfalarda_ortak_header(self):
        for adres in ["/", "/dashboard", "/profile", "/boxoffice", "/tickets", "/settings"]:
            with self.subTest(adres=adres):
                metin = self.client.get(adres).get_data(as_text=True)
                header = metin.split('<nav class="navbar"', 1)[1].split("</nav>", 1)[0]
                for baglanti in ["Anasayfa", "Profilim", "Gişe", "Biletlerim", "Ayarlar"]:
                    self.assertIn(baglanti, header)

    def test_csv_smartlead_kolonlari(self):
        sohbet = self.client.post("/api/sohbet", json={"mesaj": "Sergi öner"})
        self.client.post("/api/adaylar", json={"isim":"Deniz Kaya", "telefon":"05552223344", "mesaj":"Sergi öner", "etkilesim_id":sohbet.json["etkilesim_id"], "iletisim_izni":True, "gecmis":[{"role":"user","content":"Ücretsiz etkinlik olsun"},{"role":"assistant","content":"Hangi tür?"},{"role":"user","content":"Sergi öner"},{"role":"assistant","content":sohbet.json["cevap"]}]})
        self.client.post("/panel-giris", data={"sifre": "test123"})
        csv = self.client.get("/panel/csv").get_data(as_text=True)
        self.assertIn("Kullanıcı İsteği", csv)
        self.assertIn("Asistan Planı", csv)
        self.assertIn("Telefon", csv)
        self.assertIn("Deniz Kaya", csv)
        self.assertIn("Ücretsiz etkinlik olsun", csv)
        self.assertIn("Tam Konuşma", csv)


if __name__ == "__main__":
    unittest.main()
