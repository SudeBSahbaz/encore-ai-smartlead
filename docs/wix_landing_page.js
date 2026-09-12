/**
 * Wix Velo - ENCORE Kişisel Asistan
 *
 * Kullanıcının mesajını ENCORE Flask API'sine gönderir.
 * Sohbet geçmişini sayfa açık kaldığı sürece bellekte tutar.
 * Yapay zekâ yanıtını Wix HTML bileşenine aktarır.
 */

import { fetch } from 'wix-fetch';

const API =
  'https://encore-ai-smartlead.onrender.com';

let gecmis = [];

$w.onReady(function () {
  $w('#btnSor').onClick(() => {
    sohbetGonder();
  });
});

async function sohbetGonder() {
  const mesaj =
    $w('#inputMesaj').value.trim();

  if (!mesaj) {
    return;
  }

  $w('#btnSor').disable();
  $w('#inputMesaj').value = '';

  // Yanıt hazırlanırken HTML kutusunda bekleme mesajı gösterir.
  $w('#html1').postMessage({
    type: 'loading'
  });

  try {
    const yanit = await fetch(
      `${API}/api/sohbet`,
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          mesaj,
          gecmis
        })
      }
    );

    const veri = await yanit.json();

    if (!yanit.ok || !veri.basari) {
      throw new Error(
        veri.hata || 'Yanıt alınamadı.'
      );
    }

    gecmis.push({
      role: 'user',
      content: mesaj
    });

    gecmis.push({
      role: 'assistant',
      content: veri.cevap
    });

    // AI yanıtını scroll edilebilir HTML kutusuna gönderir.
    $w('#html1').postMessage({
      type: 'ai-response',
      text: veri.cevap
    });
  } catch (hata) {
    console.error(
      'Sohbet bağlantı hatası:',
      hata
    );

    $w('#html1').postMessage({
      type: 'ai-response',
      text: 'Bağlantı kurulamadı. Lütfen tekrar dene.'
    });
  } finally {
    $w('#btnSor').enable();
  }
}
