"""Veri katmanının İngilizce paket yolu için uyumluluk dışa aktarımları."""

from uygulama.database import asistan_etkilesimi_ekle, baglanti_al, etkilesim_sil, musteri_adayi_ekle, musteri_adayi_sil, tum_adaylari_getir, tum_etkilesimleri_getir, veritabani_baslat

get_connection = baglanti_al
initialize_database = veritabani_baslat
add_interaction = asistan_etkilesimi_ekle
get_all_interactions = tum_etkilesimleri_getir
delete_interaction = etkilesim_sil
add_lead = musteri_adayi_ekle
get_all_leads = tum_adaylari_getir
delete_lead = musteri_adayi_sil

__all__ = ["get_connection", "initialize_database", "add_interaction", "get_all_interactions", "delete_interaction", "add_lead", "get_all_leads", "delete_lead"]
