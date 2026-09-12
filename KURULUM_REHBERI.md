# ENCORE AI — Kurulum ve Wix Entegrasyon Rehberi

## Proje yapısı

Standart teslim yapısı `run.py`, `config.py`, `app/`, `docs/` ve `tests/` klasörlerinden oluşur. Türkçe isimli özgün modüller korunmuş, İngilizce yollar uyumluluk katmanı olarak eklenmiştir.

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

## Yerel kurulum

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r gereksinimler.txt

# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env

python run.py
```

Uygulama varsayılan olarak aşağıdaki adreste çalışır:

```text
http://localhost:5000
```

Kontrol adresleri:

- `GET /health`
- `POST /api/chat`
- `GET /api/interactions`
- `POST /api/leads`
- `GET /api/leads`

Türkçe uyumluluk uçları:

- `GET /saglik-durumu`
- `POST /api/sohbet`
- `GET /api/etkilesimler`
- `POST /api/adaylar`
- `GET /api/adaylar`

## Otomatik testler

Projede sağlık kontrolü, sohbet, lead kaydı, panel güvenliği, CORS, API sözleşmesi, CSV çıktısı ve arayüz davranışlarını kapsayan 18 otomatik test bulunmaktadır.

Testleri çalıştırmak için:

```bash
python -m unittest discover -s tests -v
```

Başarılı çalıştırmada 18 testin tamamının `OK` sonucu vermesi beklenir.

## Render deployment

Render üzerinde aşağıdaki ayarlar kullanılır:

- Build Command: `pip install -r gereksinimler.txt`
- Start Command: `gunicorn run:app`
- Ortam: `FLASK_ORTAMI=uretim`

Aşağıdaki değerler yalnızca Render Environment bölümünde tanımlanmalıdır:

- `SECRET_KEY`
- `ADMIN_API_KEY`
- `AI_PROVIDER`
- Seçilen AI sağlayıcısının API anahtarı
- `CORS_ALLOWED_ORIGINS`

Groq kullanılıyorsa:

```text
AI_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-20b
```

`CORS_ALLOWED_ORIGINS` değeri yayımlanmış Wix sitesinin alan adı olmalıdır.

Gerçek API anahtarları ve `.env`, `.env.example`, JavaScript dosyaları veya GitHub repository’si içine yazılmamalıdır.

## Wix Velo entegrasyonu

ENCORE Wix sitesi ile Flask backend’i arasındaki bağlantı Wix Velo aracılığıyla kurulmuştur.

### Landing ve kişisel asistan

`docs/wix_landing_page.js` dosyası, Wix üzerinde çalışan güncel kişisel asistan sayfa kodunu içerir.

Kişisel asistan bileşenleri:

- `#inputMesaj`: Kullanıcının mesajını yazdığı alan
- `#btnSor`: Mesajı yapay zekâya gönderen buton
- `#html1`: Yüklenme durumunu ve yapay zekâ yanıtını gösteren HTML bileşeni

Kişisel asistan:

1. Kullanıcının mesajını `POST /api/sohbet` adresine gönderir.
2. Önceki mesajları `gecmis` dizisiyle birlikte backend’e iletir.
3. Yanıt hazırlanırken HTML bileşeninde bekleme durumu gösterir.
4. Yapay zekâ yanıtını `postMessage()` ile HTML bileşenine aktarır.
5. `credentials: 'include'` kullanarak Flask oturumunun korunmasını sağlar.

Render API adresi:

```text
https://encore-ai-smartlead.onrender.com

### Yönetim paneli

`docs/wix_dashboard.js`, Wix yönetim panelinde kullanılan güncel sayfa kodunu içerir.

Yönetim paneli bileşenleri:

- `#leadRepeater`
- `#txtKullanici`
- `#txtTelefon`
- `#txtDurum`
- `#txtTarih`

Paneldeki arama alanı jüri demosunun görsel arayüz öğesidir. Yenile butonu ise Wix Editor üzerinden yönetim paneli sayfasına yeniden yönlendirilerek kayıtların yenilenmesini sağlar.

### Güvenli Wix backend modülü

Yönetim paneli, Render API’sine doğrudan bağlanmaz. Bunun yerine Wix backend tarafındaki `getLeads()` web metodunu kullanır.

GitHub’daki örnek dosya:

```text
docs/wix_backend_leads.web.js
```

Wix içindeki gerçek konumu:

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

Bu secret’ın değeri, Render üzerinde tanımlanan `ADMIN_API_KEY` ile aynı olmalıdır.

Gerçek anahtar hiçbir zaman Wix sayfa koduna veya GitHub repository’sine yazılmamalıdır.

## Veri akışı

```text
Ziyaretçi
   ↓
Wix kişisel asistan
   ↓
ENCORE Flask API
   ↓
SQLite veritabanı
   ↓
Wix backend web modülü
   ↓
Wix yönetim paneli
```

Kullanıcı kişisel asistanla görüştükten ve iletişim izni verdikten sonra adı, telefonu, plan durumu ve kayıt tarihi veritabanına kaydedilir. Yönetim paneli bu kayıtları güvenli Wix backend bağlantısı üzerinden görüntüler.

## Güvenlik önlemleri

Projede aşağıdaki temel güvenlik önlemleri uygulanmıştır:

- API anahtarlarının ortam değişkenlerinde tutulması
- `.env` dosyasının `.gitignore` ile korunması
- SQL sorgularında parametreli sorgular kullanılması
- CORS alan adı kontrolü
- Yönetim API’sinde `X-Admin-Key` doğrulaması
- Wix Secrets Manager kullanımı
- Telefon, isim, mesaj ve iletişim izni doğrulaması
- Yönetim panelinin Wix backend üzerinden veri alması
