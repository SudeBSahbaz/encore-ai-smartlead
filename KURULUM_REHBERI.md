# ENCORE AI — Kurulum ve Wix Entegrasyon Rehberi

## Proje yapısı

Standart teslim yapısı `run.py`, `config.py`, `app/`, `docs/` ve `tests/` klasörlerinden oluşur. Türkçe isimli özgün modüller korunmuş, İngilizce yollar uyumluluk katmanı olarak eklenmiştir.

## Yerel kurulum

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r gereksinimler.txt
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env
python run.py
```

Kontrol adresleri:

- `http://localhost:5000/health`
- `POST http://localhost:5000/api/chat`
- `GET http://localhost:5000/api/interactions`
- `POST http://localhost:5000/api/leads`
- `GET http://localhost:5000/api/leads`

## Test

```bash
python -m unittest discover -s tests -v
```

## Render

- Build Command: `pip install -r gereksinimler.txt`
- Start Command: `gunicorn run:app`
- Ortam: `FLASK_ORTAMI=uretim`
- `SECRET_KEY`, `ADMIN_API_KEY` ve seçilen AI sağlayıcısının anahtarı yalnızca Render Environment bölümünde tutulur.
- Groq kullanılıyorsa `GROQ_MODEL=openai/gpt-oss-20b` tanımlanır.
- GPT-OSS modeli düşük reasoning düzeyi ve yeterli çıktı bütçesiyle çağrılır; böylece kısa konuşmalarda boş yanıt oluşmaz.
- `CORS_ALLOWED_ORIGINS` değeri yayımlanmış Wix alan adı olmalıdır.

## Wix Velo

1. Wix'te Dev Mode/Velo açılır.
2. `docs/wix_landing_page.js` ilgili B2C sayfasına eklenir.
3. `docs/wix_dashboard.js` yalnızca Wix Members yetkili rolüne açık dashboard sayfasına eklenir.
4. Her iki dosyadaki `API_BASE_URL`, Render adresiyle değiştirilir.
5. Mevcut ENCORE CSS'i, Poppins tipografisi, renkleri ve global navigasyonu değiştirilmez.

Landing bileşenleri: `#inputQuestion`, `#btnAsk`, `#textAiReply`, `#boxSavePlan`, `#inputName`, `#inputPhone`, `#checkboxConsent`, `#btnSavePlan`, `#textSaveStatus`, `#boxMembershipInvite`, `#btnJoin`, `#btnLater`.

Dashboard bileşenleri: `#repeaterLeads`, `#textLeadName`, `#textLeadPhone`, `#textUserRequest`, `#textAiPlan`, `#textLeadStatus`, `#textLeadDate`, `#textTotalCount`, `#btnRefresh`, `#textLoadingStatus`, `#inputSearch`.

Üretimde etkileşim listeleme çağrısı doğrudan tarayıcıda gizli anahtar taşımamalıdır. Wix backend web modülü üzerinden `X-Admin-Key` eklenerek proxy edilmelidir.
