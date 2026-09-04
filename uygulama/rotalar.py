import csv
import io
import json
import re
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, session, url_for

from uygulama.database import (
    asistan_etkilesimi_ekle,
    etkilesim_oturuma_ait_mi,
    etkilesim_sil,
    musteri_adayi_ekle,
    musteri_adayi_sil,
    tum_adaylari_getir,
    tum_etkilesimleri_getir,
)
from uygulama.servisler.yapay_zeka_servisi import YapayZekaServisHatasi, yapay_zeka_servisi

api_arayuzu = Blueprint("api", __name__)
sayfa_arayuzu = Blueprint("sayfalar", __name__)

def panel_girisi_gerekli(fonksiyon):
    @wraps(fonksiyon)
    def sarmal(*args, **kwargs):
        if not session.get("panel_yetkili"):
            return redirect(url_for("sayfalar.panel_giris", sonraki=request.path))
        return fonksiyon(*args, **kwargs)
    return sarmal


def _api_yetkili():
    if session.get("panel_yetkili"):
        return True
    beklenen = current_app.config.get("ADMIN_API_KEY", "")
    gelen = request.headers.get("X-Admin-Key", "")
    return bool(beklenen and gelen == beklenen)


def _telefon_temizle(deger):
    deger = re.sub(r"[^\d+]", "", deger or "")
    if deger.startswith("00"):
        deger = "+" + deger[2:]
    return deger


def _etkilesim_ingilizce(etkilesim):
    return {
        "id": etkilesim["id"],
        "session_code": etkilesim["oturum_kodu"],
        "user_message": etkilesim["kullanici_mesaji"],
        "assistant_reply": etkilesim["asistan_yaniti"],
        "provider": etkilesim["saglayici"],
        "successful": bool(etkilesim["basarili"]),
        "created_at": etkilesim["olusturulma_tarihi"],
    }


def _oturum_kodu():
    if "asistan_oturum_kodu" not in session:
        session["asistan_oturum_kodu"] = f"ENC-{secrets.token_hex(3).upper()}"
    return session["asistan_oturum_kodu"]


def _sohbet_hazirla(ham_gecmis):
    temiz = []
    if isinstance(ham_gecmis, list):
        for oge in ham_gecmis[-20:]:
            if not isinstance(oge, dict) or oge.get("role") not in {"user", "assistant"}:
                continue
            icerik = str(oge.get("content", "")).strip()[:2000]
            if icerik:
                temiz.append({"role": oge["role"], "content": icerik})
    kullanici_mesajlari = [oge["content"] for oge in temiz if oge["role"] == "user"]
    ozet = " • ".join(kullanici_mesajlari)
    if len(ozet) > 1200:
        ozet = ozet[:1197].rstrip() + "…"
    return temiz, ozet


@sayfa_arayuzu.get("/")
def ana_sayfa():
    return render_template("index.html", isletme=current_app.config["BUSINESS_NAME"])


@sayfa_arayuzu.get("/dashboard")
def kullanici_paneli():
    return render_template("kullanici_dashboard.html")


@sayfa_arayuzu.get("/kesfet")
def kesfet():
    return redirect(url_for("sayfalar.ana_sayfa", _anchor="etkinlikler"))


@sayfa_arayuzu.get("/boxoffice")
@sayfa_arayuzu.get("/box-office")
def gise():
    return render_template("gise.html")


@sayfa_arayuzu.get("/profil")
@sayfa_arayuzu.get("/profile")
def profil():
    return render_template("profil.html")


@sayfa_arayuzu.get("/favoriler")
@sayfa_arayuzu.get("/favorites")
def favoriler():
    return redirect(url_for("sayfalar.profil", _anchor="tercihler"))


@sayfa_arayuzu.get("/biletlerim")
@sayfa_arayuzu.get("/tickets")
def biletler():
    return render_template("biletler.html")


@sayfa_arayuzu.get("/odeme")
@sayfa_arayuzu.get("/checkout")
def odeme():
    return redirect(url_for("sayfalar.gise"))


@sayfa_arayuzu.get("/abonelik")
@sayfa_arayuzu.get("/subscription")
def abonelik():
    return redirect(url_for("sayfalar.profil", _anchor="abonelik"))


@sayfa_arayuzu.get("/ayarlar")
@sayfa_arayuzu.get("/settings")
def ayarlar():
    return render_template("ayarlar.html")


@sayfa_arayuzu.route("/panel-giris", methods=["GET", "POST"])
def panel_giris():
    hata = None
    if request.method == "POST":
        if request.form.get("sifre") == current_app.config["PANEL_PASSWORD"]:
            session["panel_yetkili"] = True
            return redirect(url_for("sayfalar.panel"))
        hata = "Şifre hatalı. Lütfen yeniden deneyin."
    return render_template("panel_giris.html", hata=hata)


@sayfa_arayuzu.post("/panel-cikis")
def panel_cikis():
    session.clear()
    return redirect(url_for("sayfalar.ana_sayfa"))


@sayfa_arayuzu.get("/panel")
@panel_girisi_gerekli
def panel():
    etkilesimler = tum_etkilesimleri_getir()
    adaylar = tum_adaylari_getir()
    for aday in adaylar:
        try:
            aday["sohbet_mesajlari"] = json.loads(aday.get("sohbet_gecmisi") or "[]")
        except (TypeError, json.JSONDecodeError):
            aday["sohbet_mesajlari"] = []
    simdi = datetime.now(timezone.utc)
    bugun = simdi.strftime("%Y-%m-%d")
    ozet = {
        "toplam": len(etkilesimler),
        "kayitli_plan": len(adaylar),
        "bugun": sum(1 for a in adaylar if str(a["olusturulma_tarihi"]).startswith(bugun)),
        "donusum": round(100 * len(adaylar) / len(etkilesimler)) if etkilesimler else 0,
    }
    return render_template("dashboard.html", adaylar=adaylar, ozet=ozet)


@sayfa_arayuzu.get("/panel/csv")
@panel_girisi_gerekli
def csv_indir():
    tampon = io.StringIO()
    yazici = csv.writer(tampon)
    yazici.writerow(["ID", "İsim", "Telefon", "Oturum", "Kullanıcı İsteği / Sohbet Özeti", "Tam Konuşma", "Asistan Planı", "İletişim İzni", "Durum", "Tarih"])
    for a in tum_adaylari_getir():
        tam_konusma = ""
        try:
            tam_konusma = "\n".join(
                f'{"Kullanıcı" if oge.get("role") == "user" else "ENCORE AI"}: {oge.get("content", "")}'
                for oge in json.loads(a.get("sohbet_gecmisi") or "[]")
            )
        except (TypeError, json.JSONDecodeError):
            pass
        yazici.writerow([a["id"], a["isim"], a["telefon"], a["oturum_kodu"] or "", a["sohbet_ozeti"] or a["kullanici_mesaji"] or a["mesaj"] or "", tam_konusma, a["asistan_yaniti"] or "", "Evet" if a["iletisim_izni"] else "Hayır", a["durum"], a["olusturulma_tarihi"]])
    return Response("\ufeff" + tampon.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=encore_potansiyel_musteriler.csv"})


@sayfa_arayuzu.get("/saglik-durumu")
def saglik_durumu():
    return jsonify({"durum": "çalışıyor", "servis": f'{current_app.config["BUSINESS_NAME"]} AI', "surum": "1.1.0"})


@sayfa_arayuzu.get("/health")
def health():
    return jsonify({"status": "ok", "service": f'{current_app.config["BUSINESS_NAME"]} AI', "version": "1.1.0"})


@api_arayuzu.post("/sohbet")
def sohbet_et():
    veri = request.get_json(silent=True) or {}
    mesaj = str(veri.get("mesaj", "")).strip()
    if not mesaj:
        return jsonify({"basari": False, "hata": "Mesaj boş olamaz."}), 400
    if len(mesaj) > 1200:
        return jsonify({"basari": False, "hata": "Mesaj en fazla 1200 karakter olabilir."}), 400
    try:
        yanit = yapay_zeka_servisi.yanit_uret(mesaj, veri.get("gecmis", []))
        kayit = asistan_etkilesimi_ekle(_oturum_kodu(), mesaj, yanit, current_app.config.get("AI_PROVIDER", "demo"), True)
        return jsonify({"basari": True, "cevap": yanit, "etkilesim_id": kayit})
    except YapayZekaServisHatasi as hata:
        asistan_etkilesimi_ekle(_oturum_kodu(), mesaj, str(hata), current_app.config.get("AI_PROVIDER", "demo"), False)
        return jsonify({"basari": False, "hata": str(hata)}), 503


@api_arayuzu.post("/chat")
def chat():
    veri = request.get_json(silent=True) or {}
    mesaj = str(veri.get("message", "")).strip()
    if not mesaj:
        return jsonify({"success": False, "error": "Message is required."}), 400
    if len(mesaj) > 1200:
        return jsonify({"success": False, "error": "Message must not exceed 1200 characters."}), 400
    try:
        yanit = yapay_zeka_servisi.yanit_uret(mesaj, veri.get("history", []))
        kayit = asistan_etkilesimi_ekle(_oturum_kodu(), mesaj, yanit, current_app.config.get("AI_PROVIDER", "demo"), True)
        return jsonify({"success": True, "reply": yanit, "interaction_id": kayit})
    except YapayZekaServisHatasi as hata:
        asistan_etkilesimi_ekle(_oturum_kodu(), mesaj, str(hata), current_app.config.get("AI_PROVIDER", "demo"), False)
        return jsonify({"success": False, "error": str(hata)}), 503


@api_arayuzu.get("/etkilesimler")
def etkilesimler():
    if not _api_yetkili():
        return jsonify({"basari": False, "hata": "Yetkisiz erişim."}), 401
    liste = tum_etkilesimleri_getir()
    return jsonify({"basari": True, "toplam": len(liste), "etkilesimler": liste})


@api_arayuzu.get("/interactions")
def interactions():
    if current_app.config.get("REQUIRE_ADMIN_API_AUTH") and not _api_yetkili():
        return jsonify({"success": False, "error": "Unauthorized."}), 401
    liste = [_etkilesim_ingilizce(e) for e in tum_etkilesimleri_getir()]
    return jsonify({"success": True, "count": len(liste), "interactions": liste})


@api_arayuzu.route("/adaylar", methods=["GET", "POST"])
def adaylar():
    if request.method == "GET":
        if not _api_yetkili():
            return jsonify({"basari": False, "hata": "Yetkisiz erişim."}), 401
        liste = tum_adaylari_getir()
        return jsonify({"basari": True, "toplam": len(liste), "adaylar": liste})

    veri = request.get_json(silent=True) or {}
    isim = str(veri.get("isim", "")).strip()
    telefon = _telefon_temizle(str(veri.get("telefon", "")))
    mesaj = str(veri.get("mesaj", "")).strip()
    sohbet_gecmisi, sohbet_ozeti = _sohbet_hazirla(veri.get("gecmis", []))
    iletisim_izni = veri.get("iletisim_izni") is True
    try:
        etkilesim_id = int(veri.get("etkilesim_id"))
    except (TypeError, ValueError):
        etkilesim_id = 0
    hatalar = {}
    if not 2 <= len(isim) <= 100:
        hatalar["isim"] = "İsim 2-100 karakter arasında olmalıdır."
    if not re.fullmatch(r"\+?\d{10,15}", telefon):
        hatalar["telefon"] = "Geçerli bir telefon numarası girin."
    if not iletisim_izni:
        hatalar["iletisim_izni"] = "Planı kaydetmek için iletişim izni gereklidir."
    if not etkilesim_oturuma_ait_mi(etkilesim_id, _oturum_kodu()):
        hatalar["etkilesim_id"] = "Önce kişisel asistanla bir plan oluşturun."
    if len(mesaj) > 1000:
        hatalar["mesaj"] = "Mesaj en fazla 1000 karakter olabilir."
    if not sohbet_gecmisi or not sohbet_ozeti:
        hatalar["gecmis"] = "Sohbet geçmişi bulunamadı."
    if hatalar:
        return jsonify({"basari": False, "hata": "Alanları kontrol edin.", "alanlar": hatalar}), 400
    kimlik = musteri_adayi_ekle(isim, telefon, mesaj, etkilesim_id, iletisim_izni, sohbet_ozeti, json.dumps(sohbet_gecmisi, ensure_ascii=False))
    return jsonify({"basari": True, "mesaj": "Planın başarıyla kaydedildi.", "id": kimlik, "uyelik_daveti": True}), 201


@api_arayuzu.route("/leads", methods=["GET", "POST"])
def leads():
    if request.method == "GET":
        if current_app.config.get("REQUIRE_ADMIN_API_AUTH") and not _api_yetkili():
            return jsonify({"success": False, "error": "Unauthorized."}), 401
        liste = tum_adaylari_getir()
        return jsonify({"success": True, "count": len(liste), "leads": liste})
    veri = request.get_json(silent=True) or {}
    name = str(veri.get("name", "")).strip()
    phone = _telefon_temizle(str(veri.get("phone", "")))
    message = str(veri.get("message", "")).strip()
    conversation, conversation_summary = _sohbet_hazirla(veri.get("history", []))
    consent = veri.get("consent") is True
    try:
        interaction_id = int(veri.get("interaction_id"))
    except (TypeError, ValueError):
        interaction_id = 0
    errors = {}
    if not 2 <= len(name) <= 100:
        errors["name"] = "Name must be between 2 and 100 characters."
    if not re.fullmatch(r"\+?\d{10,15}", phone):
        errors["phone"] = "Enter a valid phone number."
    if not consent:
        errors["consent"] = "Consent is required."
    if not etkilesim_oturuma_ait_mi(interaction_id, _oturum_kodu()):
        errors["interaction_id"] = "Create a personal plan first."
    if len(message) > 1000:
        errors["message"] = "Message must not exceed 1000 characters."
    if not conversation or not conversation_summary:
        errors["history"] = "Conversation history is required."
    if errors:
        return jsonify({"success": False, "error": "Check the fields.", "fields": errors}), 400
    kimlik = musteri_adayi_ekle(name, phone, message, interaction_id, consent, conversation_summary, json.dumps(conversation, ensure_ascii=False))
    return jsonify({"success": True, "message": "Your plan was saved.", "lead": {"id": kimlik}, "membership_invitation": True}), 201


@api_arayuzu.delete("/leads/<int:kimlik>")
def lead_sil(kimlik):
    if not _api_yetkili():
        return jsonify({"success": False, "error": "Unauthorized."}), 401
    if not musteri_adayi_sil(kimlik):
        return jsonify({"success": False, "error": "Lead not found."}), 404
    return jsonify({"success": True, "message": "Lead deleted."})


@api_arayuzu.delete("/interactions/<int:kimlik>")
def interaction_sil(kimlik):
    if not _api_yetkili():
        return jsonify({"success": False, "error": "Unauthorized."}), 401
    if not etkilesim_sil(kimlik):
        return jsonify({"success": False, "error": "Interaction not found."}), 404
    return jsonify({"success": True, "message": "Interaction deleted."})
