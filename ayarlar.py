import os
from pathlib import Path

from dotenv import load_dotenv

TABAN_DIZIN = Path(__file__).resolve().parent
load_dotenv(TABAN_DIZIN / ".env")


class Ayarlar:
    SECRET_KEY = os.environ.get("SECRET_KEY", "yalnizca-gelistirme-icin-degistirin")
    DATABASE_URL = os.environ.get("DATABASE_URL", str(TABAN_DIZIN / "akilli_satis.db"))
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "demo").lower()
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "ENCORE")
    BUSINESS_CONTEXT = os.environ.get(
        "BUSINESS_CONTEXT",
        "ENCORE'un kultur-sanat kesif asistanisin. Kullanicinin ilgi alani, tarih, konum, butce ve "
        "ulasim tercihlerini anlayarak konser, tiyatro, sergi ve atolye onerileri sun. Turkce, sicak, "
        "kisa ve net yanit ver; etkinlik bilgisi uydurma ve yeterli bilgi yoksa tercih sorusu sor.",
    )
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5000")
    PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD", "encore2026")
    ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
    REQUIRE_ADMIN_API_AUTH = False
    JSON_AS_ASCII = False
    MAX_CONTENT_LENGTH = 32 * 1024


class GelistirmeAyarlari(Ayarlar):
    DEBUG = True
    TESTING = False


class UretimAyarlari(Ayarlar):
    DEBUG = False
    REQUIRE_ADMIN_API_AUTH = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # Wix ve Render farklı alan adlarında çalıştığı için oturum çerezi
    # yalnızca HTTPS üzerinden çapraz alan isteklerinde de gönderilebilmelidir.
    SESSION_COOKIE_SAMESITE = "None"


class TestAyarlari(Ayarlar):
    TESTING = True
    DATABASE_URL = ":memory:"
    AI_PROVIDER = "demo"
    WTF_CSRF_ENABLED = False


ayar_secici = {
    "gelistirme": GelistirmeAyarlari,
    "uretim": UretimAyarlari,
    "test": TestAyarlari,
}
