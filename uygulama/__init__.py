import os

from flask import Flask
from flask_cors import CORS

from ayarlar import ayar_secici
from uygulama.database import veritabani_baslat


def _cors_kokenleri(deger):
    if deger == "*":
        return "*"
    return [k.strip() for k in deger.split(",") if k.strip()]


def uygulama_olustur(ayar_adi=None, ek_ayarlar=None):
    uygulama = Flask(__name__, template_folder="sablonlar", static_folder="statik")
    secilen_ayar = ayar_adi or os.environ.get("FLASK_ORTAMI", "gelistirme")
    secilen = ayar_secici.get(secilen_ayar, ayar_secici["gelistirme"])
    uygulama.config.from_object(secilen)
    if ek_ayarlar:
        uygulama.config.update(ek_ayarlar)

    CORS(
        uygulama,
        resources={r"/api/*": {"origins": _cors_kokenleri(uygulama.config["CORS_ALLOWED_ORIGINS"]) }},
        methods=["GET", "POST", "OPTIONS"],
        supports_credentials=True,
    )
    veritabani_baslat(uygulama)

    from uygulama.rotalar import api_arayuzu, sayfa_arayuzu
    uygulama.register_blueprint(api_arayuzu, url_prefix="/api")
    uygulama.register_blueprint(sayfa_arayuzu)
    return uygulama
