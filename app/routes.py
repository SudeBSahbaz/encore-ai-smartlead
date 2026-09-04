"""Blueprint'lerin İngilizce paket yolu için uyumluluk dışa aktarımları."""

from uygulama.rotalar import api_arayuzu, sayfa_arayuzu

api_blueprint = api_arayuzu
pages_blueprint = sayfa_arayuzu

__all__ = ["api_blueprint", "pages_blueprint"]
