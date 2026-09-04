# ENCORE AI

ENCORE Wix sitesi için geliştirilen yapay zekâ destekli kişisel kültür-sanat keşif asistanı ve SmartLead dönüşüm backend'i.

Kod, hocanın istediği İngilizce standart dosya/API adlarını ve önceki Türkçe uçları birlikte destekler. ENCORE'a özgü yapay zekâ davranışı yalnızca `BUSINESS_CONTEXT` ortam değişkenindedir; servis kodu başka işletmelere yeniden uyarlanabilir.

## Hızlı başlangıç

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r gereksinimler.txt
copy .env.example .env
python run.py
```

Mac/Linux için aktivasyon komutu `source venv/bin/activate`, kopyalama komutu `cp .env.example .env` şeklindedir.

- Ana sayfa: http://localhost:5000
- Eski ENCORE B2B dashboard (geliştirme): http://localhost:5000/dashboard
- Profil (geliştirme): http://localhost:5000/profile
- Gişe (geliştirme): http://localhost:5000/boxoffice
- Biletlerim (geliştirme): http://localhost:5000/tickets
- Ayarlar (geliştirme): http://localhost:5000/settings
- Panel: http://localhost:5000/panel
- Sağlık kontrolü: http://localhost:5000/health
- Örnek panel şifresi: `encore2026` (canlı ortamda değiştirin)

## Test

```bash
python -m unittest discover -s tests -v
```

## Render

- Build: `pip install -r gereksinimler.txt`
- Start: `gunicorn run:app`
- `FLASK_ORTAMI=uretim` ve tüm sırlar Render Environment alanında tanımlanmalıdır.

## API sözleşmesi

- `GET /health`
- `POST /api/chat` — `{ "message": "...", "history": [] }`
- `GET /api/interactions` — anonim asistan etkileşimleri; üretimde oturum veya `X-Admin-Key` gerektirir
- `POST /api/leads` — başarılı bir asistan etkileşiminden sonra planı iletişim bilgileriyle kaydeder
- `GET /api/leads` — potansiyel müşterileri listeler; üretimde oturum veya `X-Admin-Key` gerektirir

Türkçe uçlar: `/saglik-durumu`, `/api/sohbet`, `/api/etkilesimler`, `/api/adaylar`.

## Arayüz kapsamı

Ana sayfadaki yapay zekâ sohbeti çalışır durumdadır. Her sohbet anonim oturum koduyla kaydedilir. Başarılı bir plan üretildikten sonra kullanıcı isterse aynı sohbet kartından adını, telefonunu ve iletişim iznini girerek planını kaydeder; böylece konuşma ile potansiyel müşteri kaydı birbirine bağlanır. Başarılı kaydın ardından küçük üyelik bağlantısı görünür ve kullanıcı Profilim sayfasına yönlendirilebilir. Şifre korumalı `/panel`; toplam sohbeti, kaydedilen planı, bugünkü lead sayısını ve dönüşüm oranını gösterir. Çok mesajlı görüşmeler kullanıcı mesajlarının birleşik özetiyle listelenir ve “Tüm konuşmayı görüntüle” alanından eksiksiz açılabilir; CSV çıktısı da özet ile tam konuşmayı içerir. Etkinlik vitrini ve eski ENCORE prototipinden aktarılan geliştirme sayfaları korunmuştur.
