const $ = (s) => document.querySelector(s);
const mesajlar = $('#mesajlar');
let gecmis = [];
let sonEtkilesimId = null;
let planKaydedildi = false;

function balon(metin, tur) {
  const div = document.createElement('div');
  div.className = `bubble ${tur}`;
  div.textContent = metin;
  mesajlar.appendChild(div);
  mesajlar.scrollTop = mesajlar.scrollHeight;
  return div;
}

function yanitMetniniTemizle(metin) {
  return String(metin || '')
    .replace(/^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$/gm, '')
    .replace(/\*\*/g, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*>\s?/gm, '')
    .replace(/\s*\|\s*/g, ' · ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

async function sohbetGonder() {
  const input = $('#sohbetMesaj');
  const mesaj = input.value.trim();
  if (!mesaj) return;
  input.value = '';
  balon(mesaj, 'user');
  const bekleme = balon('Yanıt hazırlanıyor…', 'bot');
  try {
    const cevap = await fetch('/api/sohbet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({mesaj, gecmis})});
    const veri = await cevap.json();
    const temizCevap = veri.basari ? yanitMetniniTemizle(veri.cevap) : veri.hata;
    bekleme.textContent = temizCevap || 'Yanıt oluşturulamadı. Lütfen yeniden deneyin.';
    if (veri.basari) {
      gecmis.push({role:'user',content:mesaj},{role:'assistant',content:temizCevap});
      sonEtkilesimId = veri.etkilesim_id;
      if (!planKaydedildi) $('#planSavePrompt').hidden = false;
    }
  } catch (_) { bekleme.textContent = 'Bağlantı kurulamadı. Lütfen yeniden deneyin.'; }
}

$('#sohbetGonder')?.addEventListener('click', sohbetGonder);
$('#sohbetMesaj')?.addEventListener('keydown', e => { if(e.key === 'Enter') sohbetGonder(); });

document.querySelectorAll('[data-focus-chat]').forEach(button => button.addEventListener('click', () => {
  document.querySelector('#assistant')?.scrollIntoView({behavior:'smooth', block:'center'});
  setTimeout(() => $('#sohbetMesaj')?.focus(), 350);
}));

document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
  const input = $('#sohbetMesaj');
  if (!input) return;
  input.value = button.dataset.prompt;
  input.focus();
}));

$('#planSaveOpen')?.addEventListener('click', () => {
  $('#planSavePrompt').hidden = true;
  $('#planSaveForm').hidden = false;
  $('#planSaveForm input[name="isim"]')?.focus();
});

$('#planSaveClose')?.addEventListener('click', () => {
  $('#planSaveForm').hidden = true;
  $('#planSavePrompt').hidden = false;
});

$('#planSaveForm')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const durum = $('#planSaveStatus');
  const button = form.querySelector('button[type="submit"]');
  const alanlar = new FormData(form);
  const veri = {
    isim: alanlar.get('isim'),
    telefon: alanlar.get('telefon'),
    mesaj: gecmis.at(-2)?.content || '',
    etkilesim_id: sonEtkilesimId,
    iletisim_izni: alanlar.get('iletisim_izni') === 'on',
    gecmis
  };
  durum.textContent = 'Planın kaydediliyor…';
  button.disabled = true;
  try {
    const cevap = await fetch('/api/adaylar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(veri)});
    const sonuc = await cevap.json();
    if (!cevap.ok || !sonuc.basari) {
      durum.textContent = sonuc.hata || 'Plan kaydedilemedi.';
      return;
    }
    planKaydedildi = true;
    form.reset();
    form.hidden = true;
    $('#planSavePrompt').hidden = true;
    $('#membershipInvite').hidden = false;
  } catch (_) {
    durum.textContent = 'Bağlantı kurulamadı. Lütfen yeniden dene.';
  } finally {
    button.disabled = false;
  }
});

$('#eventSearchInput')?.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const query = e.currentTarget.value.trim();
  if (!query) return;
  window.location.href = `/kesfet?arama=${encodeURIComponent(query)}`;
});

const CART_KEY = 'encoreGise';

function sepetiOku() {
  try { return JSON.parse(localStorage.getItem(CART_KEY) || '[]'); }
  catch (_) { return []; }
}

function sepetiYaz(sepet) {
  localStorage.setItem(CART_KEY, JSON.stringify(sepet));
  giseDurumunuGuncelle();
}

function fiyatSayiyaCevir(fiyat) {
  const sayi = Number(String(fiyat || '').replace(/[^0-9]/g, ''));
  return Number.isFinite(sayi) ? sayi : 0;
}

function giseDurumunuGuncelle() {
  const sepet = sepetiOku();
  const kimlikler = new Set(sepet.map(item => item.id));
  document.querySelectorAll('.nav-cart-count').forEach(rozet => {
    rozet.textContent = sepet.length;
    rozet.hidden = sepet.length === 0;
  });
  document.querySelectorAll('.event-card').forEach(kart => {
    const eklendi = kimlikler.has(kart.dataset.eventId);
    kart.classList.toggle('in-cart', eklendi);
    const ikon = kart.querySelector('.ticket-toggle');
    const dugme = kart.querySelector('.add-to-boxoffice');
    ikon?.setAttribute('aria-pressed', String(eklendi));
    if (dugme) {
      dugme.textContent = '🎟';
      dugme.title = eklendi ? 'Gişeden çıkar' : 'Gişeye ekle';
      dugme.setAttribute('aria-label', dugme.title);
    }
  });
  giseSayfasiniCiz(sepet);
}

function etkinlikDegistir(kart) {
  const sepet = sepetiOku();
  const id = kart.dataset.eventId;
  const index = sepet.findIndex(item => item.id === id);
  const ekleniyor = index < 0;
  if (!ekleniyor) sepet.splice(index, 1);
  else sepet.push({id, title:kart.dataset.title, price:kart.dataset.price});
  sepetiYaz(sepet);
  bildirimGoster(ekleniyor ? 'Bilet gişede' : 'Bilet gişeden çıkarıldı');
}

let bildirimZamanlayicisi;
function bildirimGoster(mesaj) {
  let bildirim = document.querySelector('.boxoffice-toast');
  if (!bildirim) {
    bildirim = document.createElement('div');
    bildirim.className = 'boxoffice-toast';
    bildirim.setAttribute('role', 'status');
    bildirim.setAttribute('aria-live', 'polite');
    document.body.appendChild(bildirim);
  }
  window.clearTimeout(bildirimZamanlayicisi);
  bildirim.textContent = mesaj;
  bildirim.classList.remove('visible');
  window.requestAnimationFrame(() => window.requestAnimationFrame(() => bildirim.classList.add('visible')));
  bildirimZamanlayicisi = window.setTimeout(() => bildirim.classList.remove('visible'), 1900);
}

document.querySelectorAll('.event-card').forEach(kart => {
  kart.querySelector('.ticket-toggle')?.addEventListener('click', () => etkinlikDegistir(kart));
  kart.querySelector('.add-to-boxoffice')?.addEventListener('click', () => etkinlikDegistir(kart));
});

function giseSayfasiniCiz(sepet) {
  const alan = $('#boxofficeItems');
  if (!alan) return;
  const adet = $('#boxofficeItemCount');
  if (adet) adet.textContent = `${sepet.length} etkinlik`;
  if (!sepet.length) {
    alan.innerHTML = '<div class="empty-state">Henüz gişeye etkinlik eklemedin.<a href="/#etkinlikler">Etkinlikleri keşfet</a></div>';
  } else {
    alan.innerHTML = sepet.map(item => `<article class="boxoffice-item"><div class="boxoffice-thumb"></div><div><h3>${item.title}</h3><p>Yakında · İstanbul</p></div><strong>${item.price}</strong><button class="remove-cart-item" type="button" data-remove-id="${item.id}" aria-label="Etkinliği kaldır">×</button></article>`).join('');
    alan.querySelectorAll('[data-remove-id]').forEach(button => button.addEventListener('click', () => sepetiYaz(sepet.filter(item => item.id !== button.dataset.removeId))));
  }
  const toplam = sepet.reduce((sum,item) => sum + fiyatSayiyaCevir(item.price), 0);
  if ($('#subtotal')) $('#subtotal').textContent = `${toplam.toLocaleString('tr-TR')} TL`;
  if ($('#grandTotal')) $('#grandTotal').textContent = `${toplam.toLocaleString('tr-TR')} TL`;
}

document.querySelector('.slider-arrow.previous')?.addEventListener('click', () => $('#eventsTrack')?.scrollBy({left:-620,behavior:'smooth'}));
document.querySelector('.slider-arrow.next')?.addEventListener('click', () => $('#eventsTrack')?.scrollBy({left:620,behavior:'smooth'}));
document.querySelectorAll('.category-chip').forEach(chip => chip.addEventListener('click', () => {
  document.querySelectorAll('.category-chip').forEach(item => item.classList.remove('active'));
  chip.classList.add('active');
}));

const etkinlikSeridi = $('#eventsTrack');
let otomatikKaydirmaDuraklatildi = false;
if (etkinlikSeridi) {
  etkinlikSeridi.addEventListener('mouseenter', () => { otomatikKaydirmaDuraklatildi = true; });
  etkinlikSeridi.addEventListener('mouseleave', () => { otomatikKaydirmaDuraklatildi = false; });
  etkinlikSeridi.addEventListener('focusin', () => { otomatikKaydirmaDuraklatildi = true; });
  etkinlikSeridi.addEventListener('focusout', () => { otomatikKaydirmaDuraklatildi = false; });
  window.setInterval(() => {
    if (otomatikKaydirmaDuraklatildi) return;
    const sonaGeldi = etkinlikSeridi.scrollLeft + etkinlikSeridi.clientWidth >= etkinlikSeridi.scrollWidth - 8;
    etkinlikSeridi.scrollTo({left: sonaGeldi ? 0 : etkinlikSeridi.scrollLeft + 301, behavior:'smooth'});
  }, 3200);
}

document.querySelectorAll('[data-settings-tab]').forEach(button => button.addEventListener('click', () => {
  const hedef = button.dataset.settingsTab;
  document.querySelectorAll('[data-settings-tab]').forEach(item => item.classList.toggle('active', item === button));
  document.querySelectorAll('[data-settings-pane]').forEach(pane => pane.classList.toggle('active', pane.dataset.settingsPane === hedef));
}));

giseDurumunuGuncelle();
