import re

import requests
from flask import current_app


class YapayZekaServisHatasi(RuntimeError):
    pass


class YapayZekaServisi:
    GORUSME_PROTOKOLU = """
ENCORE GÖRÜŞME PROTOKOLÜ:
- Bu uygulamaya şu anda canlı veya doğrulanmış etkinlik veri kaynağı bağlı DEĞİLDİR. Bu nedenle
  hiçbir koşulda örnek dahi olsa sanatçı, etkinlik, mekân, tarih, saat, fiyat ya da bilet bilgisi üretme.
  Kullanıcı senden doğrudan liste istese bile doğrulanmış veri olmadan liste veremeyeceğini söyle.
- Öneri hazırlamadan önce konuşmanın tamamından şu bilgileri netleştir: etkinlik türü/ilgi alanı;
  şehir, ilçe ve gidilebilecek mesafe; kesin uygun gün veya tarih ve saat aralığı; toplam bütçe;
  ulaşım tercihi.
- Kullanıcının uygunluğunu açık uçlu sor: "Hangi gün veya günlerde, hangi saat aralıklarında
  müsaitsin?" Kullanıcı söylemeden belirli bir gün, hafta içi veya hafta sonu varsayma ve seçenek
  dayatma. Yalnızca kullanıcı "hafta sonu" derse hangi hafta sonu günü/günleri ve saat aralığını
  netleştir.
- "Haftanın herhangi bir günü", "her gün", "gün fark etmez" veya benzeri bir ifade kesin gün
  uygunluğu sayılır. Yanında saat aralığı da varsa müsaitlik TAMAMLANMIŞTIR; belirli gün seçmesini
  isteme, cuma/cumartesi/pazar gibi örnekler verme ve bu bilgiyi yeniden sorma.
- Kullanıcının son mesajını önceki mesajlarla birlikte değerlendir. Daha önce verilmiş ya da
  "herhangi biri/fark etmez" şeklinde açıkça esnek bırakılmış bir tercihi eksik kabul etme.
- Eksik bilgileri tekrar sorma. Bir yanıtta en fazla iki eksik bilgi konusu sor; üçüncü konuyu sonraki
  mesaja bırak. Zorunlu bilgiler tamamlanmadan etkinlik listesi veya kesin plan üretme.
- Sisteme doğrulanmış canlı etkinlik verisi sağlanmadıysa sanatçı, etkinlik, mekân, tarih, saat,
  fiyat veya bilet bilgisi uydurma. Bunun yerine tercih profilini özetle ve canlı veri bağlantısının
  ardından doğrulanmış seçeneklerin sunulacağını açıkça belirt.
- Türkçe, sıcak, kısa ve doğrudan yaz. Normal sohbet metni kullan. Markdown tablosu, dikey çizgi,
  yıldızla kalınlaştırma veya karmaşık başlık kullanma. Soru yanıtları 120 kelimeyi geçmesin.
"""

    @staticmethod
    def _yaniti_temizle(metin):
        """Model talimata rağmen Markdown döndürürse kullanıcıya düz metin gösterir."""
        satirlar = []
        for ham_satir in str(metin or "").splitlines():
            satir = ham_satir.strip()
            if not satir:
                if satirlar and satirlar[-1] != "":
                    satirlar.append("")
                continue
            if re.fullmatch(r"\|?(?:\s*:?-{3,}:?\s*\|)+\s*", satir):
                continue
            satir = re.sub(r"^#{1,6}\s*", "", satir)
            satir = re.sub(r"^>\s*", "", satir)
            satir = satir.replace("**", "").replace("__", "")
            if "|" in satir:
                hucreler = [hucre.strip() for hucre in satir.strip("|").split("|") if hucre.strip()]
                satir = " - ".join(hucreler)
            satirlar.append(satir)
        return "\n".join(satirlar).strip()

    def yanit_uret(self, kullanici_mesaji, sohbet_gecmisi=None):
        saglayici = current_app.config.get("AI_PROVIDER", "demo").lower()
        if saglayici == "groq":
            return self._openai_uyumlu_cagir(
                "https://api.groq.com/openai/v1/chat/completions",
                current_app.config.get("GROQ_API_KEY"),
                current_app.config.get("GROQ_MODEL", "openai/gpt-oss-20b"),
                kullanici_mesaji, sohbet_gecmisi,
            )
        if saglayici == "openai":
            return self._openai_uyumlu_cagir(
                "https://api.openai.com/v1/chat/completions",
                current_app.config.get("OPENAI_API_KEY"), "gpt-4o-mini",
                kullanici_mesaji, sohbet_gecmisi,
            )
        if saglayici == "gemini":
            return self._gemini_cagir(kullanici_mesaji, sohbet_gecmisi)
        return self._demo_yaniti_ver(kullanici_mesaji)

    def _mesajlari_olustur(self, mesaj, gecmis):
        guvenli_gecmis = []
        for oge in (gecmis or [])[-10:]:
            if isinstance(oge, dict) and oge.get("role") in {"user", "assistant"}:
                guvenli_gecmis.append({"role": oge["role"], "content": str(oge.get("content", ""))[:1200]})
        tum_kullanici_metinleri = [
            oge["content"] for oge in guvenli_gecmis if oge["role"] == "user"
        ] + [str(mesaj)]
        birlesik_metin = " ".join(tum_kullanici_metinleri).casefold()
        tamamlanan_bilgiler = []
        if re.search(r"\bbu ay\b", birlesik_metin):
            tamamlanan_bilgiler.append(
                "Kullanıcı tarih dönemi olarak içinde bulunulan ayı seçti; hafta veya tarih aralığını yeniden sorma."
            )
        esnek_gun = re.search(r"haftanın herhangi bir günü|herhangi bir gün|her gün|gün fark etmez", birlesik_metin)
        saat_araligi = re.search(r"\b(?:[01]?\d|2[0-3])[.:][0-5]\d\s*[-–]\s*(?:[01]?\d|2[0-3])[.:][0-5]\d\b", birlesik_metin)
        if esnek_gun and saat_araligi:
            tamamlanan_bilgiler.append(
                "Kullanıcının gün ve saat uygunluğu tamamlandı; belirli bir gün seçmesini isteme."
            )
        durum_notu = ""
        if tamamlanan_bilgiler:
            durum_notu = "\n\nKONUŞMADAN KESİN OLARAK TAMAMLANAN BİLGİLER:\n- " + "\n- ".join(tamamlanan_bilgiler)

        return [
            {
                "role": "system",
                "content": current_app.config["BUSINESS_CONTEXT"] + "\n\n" + self.GORUSME_PROTOKOLU + durum_notu,
            },
            *guvenli_gecmis,
            {"role": "user", "content": mesaj},
        ]

    def _openai_uyumlu_cagir(self, url, anahtar, model, mesaj, gecmis):
        if not anahtar:
            return self._demo_yaniti_ver(mesaj)
        try:
            istek_govdesi = {
                "model": model,
                "messages": self._mesajlari_olustur(mesaj, gecmis),
                "temperature": 0.35,
            }
            if model.startswith("openai/gpt-oss-"):
                # GPT-OSS görünür yanıttan önce reasoning tokenları kullanır.
                istek_govdesi.update({"reasoning_effort": "low", "max_completion_tokens": 1024})
            else:
                istek_govdesi["max_completion_tokens"] = 500
            cevap = requests.post(
                url,
                headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"},
                json=istek_govdesi,
                timeout=20,
            )
            cevap.raise_for_status()
            icerik = cevap.json()["choices"][0]["message"]["content"].strip()
            if not icerik:
                raise ValueError("Yapay zekâ boş yanıt döndürdü.")
            return self._yaniti_temizle(icerik)
        except (requests.RequestException, KeyError, IndexError, ValueError) as hata:
            raise YapayZekaServisHatasi("Yapay zeka servisine su anda ulasilamiyor. Lutfen tekrar deneyin.") from hata

    def _gemini_cagir(self, mesaj, gecmis):
        anahtar = current_app.config.get("GEMINI_API_KEY")
        if not anahtar:
            return self._demo_yaniti_ver(mesaj)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={anahtar}"
        metin = current_app.config["BUSINESS_CONTEXT"] + "\n\nMusteri: " + mesaj
        try:
            cevap = requests.post(url, json={"contents": [{"parts": [{"text": metin}]}]}, timeout=20)
            cevap.raise_for_status()
            icerik = cevap.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return self._yaniti_temizle(icerik)
        except (requests.RequestException, KeyError, IndexError, ValueError) as hata:
            raise YapayZekaServisHatasi("Yapay zeka servisine su anda ulasilamiyor. Lutfen tekrar deneyin.") from hata

    def _demo_yaniti_ver(self, mesaj):
        isletme = current_app.config.get("BUSINESS_NAME", "İşletme")
        return (
            f"{isletme} asistanı demo modunda çalışıyor. Mesajınızı aldım: “{mesaj[:120]}”. "
            "Gerçek yapay zekâ yanıtı için .env dosyasında bir sağlayıcı ve API anahtarı tanımlayın."
        )


yapay_zeka_servisi = YapayZekaServisi()
