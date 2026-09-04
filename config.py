"""İngilizce dosya standardı için mevcut merkezi ayarların uyumluluk katmanı."""

from ayarlar import Ayarlar, GelistirmeAyarlari, TestAyarlari, UretimAyarlari

Config = Ayarlar
DevelopmentConfig = GelistirmeAyarlari
ProductionConfig = UretimAyarlari
TestingConfig = TestAyarlari

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
