"""Hocanın istediği ``app`` paket adı için application-factory girişi."""

from uygulama import uygulama_olustur


def create_app(config_name=None, extra_config=None):
    mapping = {
        "development": "gelistirme",
        "production": "uretim",
        "testing": "test",
    }
    return uygulama_olustur(mapping.get(config_name, config_name), extra_config)


__all__ = ["create_app"]
