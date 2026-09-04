"""Yapay zekâ servisinin İngilizce paket yolu için uyumluluk dışa aktarımları."""

from uygulama.servisler.yapay_zeka_servisi import YapayZekaServisi, YapayZekaServisHatasi, yapay_zeka_servisi

AIService = YapayZekaServisi
AIServiceError = YapayZekaServisHatasi
ai_service = yapay_zeka_servisi

__all__ = ["AIService", "AIServiceError", "ai_service"]
