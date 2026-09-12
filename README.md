# ENCORE AI

ENCORE Wix sitesi için geliştirilen yapay zekâ destekli kişisel kültür-sanat keşif asistanı ve SmartLead dönüşüm backend’idir.

Sistem, ziyaretçilerin kültür-sanat tercihlerini anlayarak kişisel öneriler oluşturur. İletişim izni veren ziyaretçilerin adı, telefon numarası ve plan durumu SmartLead kaydı olarak saklanır ve Wix üzerindeki yönetim panelinde görüntülenir.

Kod, İngilizce standart dosya ve API adlarını desteklerken önceki Türkçe API uçlarıyla uyumluluğu da korur. ENCORE’a özgü yapay zekâ davranışı `BUSINESS_CONTEXT` ortam değişkeni üzerinden yönetildiği için servis farklı işletmelere de uyarlanabilir.

## Temel özellikler

* Yapay zekâ destekli kültür-sanat keşif asistanı
* Çok mesajlı sohbet geçmişi
* Kişisel etkinlik önerileri ve plan oluşturma
* Ad ve telefon bilgileriyle SmartLead kaydı
* Açık iletişim izni kontrolü
* SQLite veritabanı
* Wix Velo entegrasyonu
* Wix Secrets Manager üzerinden güvenli yönetici anahtarı kullanımı
* Yönetim panelinde kullanıcı adı, telefon, plan durumu ve kayıt tarihi gösterimi
* CSV dışa aktarma
* Türkçe ve İngilizce API uçları
* Demo, geliştirme, test ve üretim ortamları
* 18 otomatik test

## Proje yapısı

```text
encore-ai-smartlead/
├── run.py
├── baslat.py
├── config.py
├── ayarlar.py
├── gereksinimler.txt
├── .env.example
├── app/
├── uygulama/
├── tests/
└── docs/
    ├── wix-velo.js
    ├── wix_landing_page.js
    ├── wix_dashboard.js
    └── wix_backend_leads.web.js
```

`app/` klasörü İngilizce standart uyumluluk katmanını, `uygulama/` klasörü ise projenin asıl Flask uygulamasını içerir.

## Hızlı başlangıç

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r gereksinimler.txt
copy .env.example .env
python run.py
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r gereksinimler.txt
cp .env.example .env
python run.py
```

Uygulama varsayılan olarak aşağıdaki adreste açılır:

```text
http://localhost:5000
```

Yerel geliştirme sayfaları:

* Ana sayfa: `http://localhost:5000`
* Kullanıcı dashboard’u: `http://localhost:5000/dashboard`
* Profil: `http://localhost:5000/profile`
* Gişe: `http://localhost:5000/boxoffice`
* Biletlerim: `http://localhost:5000/tickets`
* Ayarlar: `http://localhost:5000/settings`
* Flask yönetim paneli: `http://localhost:5000/panel`
* Sağlık kontrolü: `http://localhost:5000/health`

Geliştirme ortamındaki örnek panel şifresi:

```text
encore2026
```

Canlı ortamda bu şifre mutlaka değiştirilmelidir.

## Otomatik testler

Projede sağlık kontrolü, sohbet, veri kaydı, yönetim paneli, API güvenliği, CORS, CSV çıktısı ve arayüz davranışlarını kapsayan 18 otomatik test bulunur.

Testleri çalıştırmak için:

```bash
python -m unittest discover -s tests -v
```

Başarılı çalıştırmada 18 testin tamamının `OK` sonucu vermesi beklenir.

## Render deployment

Render ayarları:

* Build Command: `pip install -r gereksinimler.txt`
* Start Command: `gunicorn run:app`
* Environment: `FLASK_ORTAMI=uretim`

Aşağıdaki değerler yalnızca Render Environment bölümünde tanımlanmalıdır:

* `SECRET_KEY`
* `ADMIN_API_KEY`
* `AI_PROVIDER`
* Seçilen yapay zekâ sağlayıcısının API anahtarı
* `CORS_ALLOWED_ORIGINS`

Groq kullanılıyorsa:

```text
AI_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-20b
```

`CORS_ALLOWED_ORIGINS` değeri yayımlanmış Wix sitesinin alan adı olmalıdır.

Gerçek API anahtarları `.env.example` dosyasına, JavaScript dosyalarına veya GitHub repository’sine eklenmemelidir.

## API sözleşmesi

İngilizce API uçları:

* `GET /health`
* `POST /api/chat`
* `GET /api/interactions`
* `POST /api/leads`
* `GET /api/leads`

Sohbet isteği örneği:

```json
{
  "message": "Bu hafta sonu bir tiyatro etkinliği arıyorum.",
  "history": []
}
```

Türkçe uyumluluk uçları:

* `GET /saglik-durumu`
* `POST /api/sohbet`
* `GET /api/etkilesimler`
* `POST /api/adaylar`
* `GET /api/adaylar`

Üretim ortamında lead ve etkileşim listelerinin görüntülenmesi için geçerli bir yönetici oturumu veya `X-Admin-Key` gerekir.

## Wix Velo entegrasyonu

ENCORE’un ziyaretçi arayüzü ve SmartLead yönetim paneli Wix üzerinde hazırlanmıştır. Flask backend Render üzerinde çalışır.

### Wix kişisel asistanı

Güncel Wix kişisel asistan sayfası:

1. Kullanıcının mesajını Flask API’ye gönderir.
2. Yapay zekâ yanıtını ekrandaki HTML bileşeninde gösterir.
3. Sayfa açık kaldığı sürece sohbet geçmişini korur.
4. Yanıt hazırlanırken yüklenme durumu gösterir.
5. Flask oturumunun korunması için istekte `credentials: 'include'` kullanır.

Güncel Wix sayfa kodu:

```text
docs/wix_landing_page.js
```

Wix kişisel asistan bileşenleri:

* `#inputMesaj`
* `#btnSor`
* `#html1`

### SmartLead kaydı

SmartLead kayıt akışı Flask arayüzü üzerinden gerçekleştirilebilir.

Kullanıcı yapay zekâ ile görüştükten sonra:

1. **Planımı Kaydet** alanını açar.
2. Adını ve telefon numarasını girer.
3. İletişim iznini işaretler.
4. Planını kaydeder.
5. Başarılı kaydın ardından üyelik davetini görür.

Kayıt; sohbet etkileşimiyle ilişkilendirilerek SQLite veritabanına yazılır. Oluşturulan kayıt Wix yönetim panelinde görüntülenebilir.

### Wix yönetim paneli

Wix yönetim panelinde aşağıdaki bilgiler görüntülenir:

* Kullanıcı adı
* Telefon numarası
* Plan durumu
* Kayıt tarihi

Güncel yönetim paneli sayfa kodu:

```text
docs/wix_dashboard.js
```

Paneldeki **Yenile** butonu Wix Editor üzerinden aynı yönetim paneli sayfasına yönlendirilmiştir. Böylece sayfa yeniden açılarak kayıtların güncel hâli alınır.

Arama alanı jüri demosunda görsel arayüz öğesi olarak kullanılmaktadır.

### Güvenli backend bağlantısı

Wix yönetim paneli, gizli yönetici anahtarını frontend kodunda taşımaz. Lead kayıtları Wix backend web modülü üzerinden alınır.

GitHub’daki örnek dosya:

```text
docs/wix_backend_leads.web.js
```

Wix içerisindeki gerçek konumu:

```text
backend/leads.web.js
```

Bu modül:

1. `ENCORE_ADMIN_API_KEY` değerini Wix Secrets Manager’dan alır.
2. Render üzerindeki `GET /api/leads` adresine istek gönderir.
3. Anahtarı `X-Admin-Key` başlığıyla backend’e iletir.
4. Gelen lead kayıtlarını Wix yönetim paneline döndürür.

Wix Secrets Manager’da aşağıdaki isimle bir secret oluşturulmalıdır:

```text
ENCORE_ADMIN_API_KEY
```

Bu secret’ın değeri, Render ortamındaki aşağıdaki değişkenle aynı olmalıdır:

```text
ADMIN_API_KEY
```

Gerçek yönetici anahtarı GitHub’a veya Wix sayfa koduna yazılmaz.

## Sistem akışı

```text
Wix kişisel asistan
        ↓
ENCORE Flask API
        ↓
Flask SmartLead kayıt formu
        ↓
SQLite veritabanı
        ↓
Wix backend web modülü
        ↓
Wix yönetim paneli
```

## SmartLead kayıt testi

Yeni kayıt akışını test etmek için:

1. Render üzerindeki ENCORE Flask uygulaması açılır.
2. Kişisel asistana bir etkinlik isteği gönderilir.
3. Yapay zekâ yanıtı alındıktan sonra **Planımı Kaydet** alanı açılır.
4. Test kullanıcısının adı ve telefon numarası girilir.
5. İletişim izni işaretlenir.
6. Plan kaydedilir.
7. Wix yönetim paneli açılır.
8. **Yenile** butonuna basılır.
9. Yeni kullanıcının adı, telefonu, plan durumu ve kayıt tarihi kontrol edilir.

Bu test aşağıdaki bağlantı zincirini doğrular:

```text
Sohbet → SmartLead kaydı → SQLite → Render API → Wix backend modülü → Wix paneli
```

## Güvenlik

Projede uygulanan başlıca güvenlik önlemleri:

* API anahtarlarının ortam değişkenlerinde tutulması
* `.env` dosyasının GitHub’dan hariç tutulması
* SQL sorgularında parametreli sorgular kullanılması
* CORS alan adı kontrolü
* Yönetim API’sinde `X-Admin-Key` doğrulaması
* Wix Secrets Manager kullanımı
* İsim, telefon, mesaj ve iletişim izni doğrulaması
* Sohbet kaydı ile lead kaydının aynı oturuma ait olduğunun kontrol edilmesi

## Arayüz kapsamı

Flask arayüzünde kişisel asistan, SmartLead kayıt formu, etkinlik vitrini, kullanıcı profili, gişe, biletler, ayarlar ve şifre korumalı yönetim paneli bulunur.

Wix üzerindeki nihai jüri demosunda kişisel asistan ve SmartLead yönetim paneli, Render üzerinde çalışan Flask backend ile bağlantılıdır.
