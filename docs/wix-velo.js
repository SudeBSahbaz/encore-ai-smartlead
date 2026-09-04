import { fetch } from 'wix-fetch';
import wixLocation from 'wix-location';

const API = 'https://SIZIN-APP.onrender.com';
let gecmis = [];
let sonEtkilesimId = null;

$w.onReady(function () {
  $w('#boxPlanKaydet').collapse();
  $w('#boxUyelikDaveti').collapse();
  $w('#btnSor').onClick(sohbetGonder);
  $w('#btnPlanKaydet').onClick(planKaydet);
  $w('#btnUyeOl').onClick(() => wixLocation.to('/profil'));
  $w('#btnSimdilikDegil').onClick(() => $w('#boxUyelikDaveti').collapse());
});

async function sohbetGonder() {
  const mesaj = $w('#inputMesaj').value.trim();
  if (!mesaj) return;
  $w('#btnSor').disable();
  $w('#txtCevap').text = 'Kişisel planın hazırlanıyor…';
  try {
    const cevap = await fetch(`${API}/api/sohbet`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mesaj,gecmis})});
    const veri = await cevap.json();
    $w('#txtCevap').text = veri.basari ? veri.cevap : veri.hata;
    if (veri.basari) {
      gecmis.push({role:'user',content:mesaj},{role:'assistant',content:veri.cevap});
      sonEtkilesimId = veri.etkilesim_id;
      $w('#boxPlanKaydet').expand();
    }
  } finally { $w('#btnSor').enable(); }
}

async function planKaydet() {
  const govde = {
    isim:$w('#inputIsim').value,
    telefon:$w('#inputTelefon').value,
    mesaj:gecmis.at(-2)?.content || '',
    etkilesim_id:sonEtkilesimId,
    iletisim_izni:$w('#checkboxIzin').checked,
    gecmis
  };
  const cevap = await fetch(`${API}/api/adaylar`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(govde)});
  const veri = await cevap.json();
  $w('#txtPlanDurum').text = veri.basari ? veri.mesaj : veri.hata;
  if (veri.basari) {
    $w('#boxPlanKaydet').collapse();
    $w('#boxUyelikDaveti').expand();
  }
}
