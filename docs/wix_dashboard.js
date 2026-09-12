/**
 * Wix Velo - ENCORE Yönetim Paneli
 *
 * Lead kayıtları güvenli Wix backend modülü üzerinden alınır.
 * Arama alanı görsel amaçlıdır.
 * Yenile butonunun sayfa bağlantısı Wix Editor'da tanımlıdır.
 */

import { getLeads } from 'backend/leads.web';

$w.onReady(async function () {
  $w('#leadRepeater').onItemReady(($item, lead) => {
    $item('#txtKullanici').text =
      lead.isim || '—';

    $item('#txtTelefon').text =
      lead.telefon || '—';

    $item('#txtDurum').text =
      durumMetni(lead.durum);

    $item('#txtTarih').text =
      tarihMetni(lead.olusturulma_tarihi);
  });

  await leadleriYukle();
});

async function leadleriYukle() {
  try {
    const sonuc = await getLeads();

    const leadler = Array.isArray(sonuc.leads)
      ? sonuc.leads
      : [];

    $w('#leadRepeater').data =
      leadler.map((lead) => ({
        ...lead,
        _id: String(lead.id)
      }));
  } catch (error) {
    console.error(
      'Lead yükleme hatası:',
      error
    );

    $w('#leadRepeater').data = [{
      _id: 'baglanti-hatasi',
      isim: 'BAĞLANTI HATASI',
      telefon: '—',
      durum: 'hata',
      olusturulma_tarihi: ''
    }];
  }
}

function durumMetni(durum) {
  const durumlar = {
    uyelik_daveti_gosterildi:
      'Plan kaydedildi',
    yeni:
      'Yeni',
    iletisime_gecildi:
      'İletişime geçildi',
    donustu:
      'Dönüştü',
    hata:
      'Hata'
  };

  return durumlar[durum] ||
    durum ||
    'Yeni';
}

function tarihMetni(tarih) {
  if (!tarih) {
    return '—';
  }

  const duzeltilmisTarih =
    String(tarih).includes('T')
      ? tarih
      : String(tarih).replace(' ', 'T') + 'Z';

  const date = new Date(duzeltilmisTarih);

  if (Number.isNaN(date.getTime())) {
    return String(tarih);
  }

  return date.toLocaleDateString('tr-TR');
}
