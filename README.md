# Google Yorum Botu (Gemini)

Google İşletme Profilinize gelen yorumları okur, **sizin yazdığınız prompt'a göre**
Gemini ile cevap üretir ve yoruma cevap olarak gönderir. Cevaplanmış yorumlara dokunmaz.

## 1. Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # sonra .env dosyasını doldurun
```

## 2. Gemini API key
https://aistudio.google.com/apikey adresinden alın, `.env` içinde `GEMINI_API_KEY` alanına yazın.

## 3. Google İşletme Profili API erişimi (bir kerelik)

> ⚠️ Google bu API'yi herkese otomatik açmaz; erişim başvurusu gerekir (onay genelde birkaç gün sürer).

1. https://console.cloud.google.com adresinde bir proje oluşturun.
2. Erişim başvurusu: https://developers.google.com/my-business/content/prereqs
   (formda proje numaranızı ve işletme e-postanızı verin).
3. Onaydan sonra **APIs & Services → Library** bölümünden şunları etkinleştirin:
   - Google My Business API
   - My Business Account Management API
   - My Business Business Information API
4. **OAuth consent screen**: "External" seçin, kendi Gmail adresinizi *Test users*'a ekleyin.
5. **Credentials → Create credentials → OAuth client ID → Desktop app**.
   İndirdiğiniz JSON dosyasını proje klasörüne `client_secret.json` adıyla koyun.

## 4. Kullanım

```bash
python -m yorumbot auth        # Tarayıcı açılır, işletme sahibi hesabıyla giriş yapın
python -m yorumbot locations   # Çıkan GOOGLE_LOCATION=... satırını .env'ye yapıştırın
python -m yorumbot test --stars 2 --comment "Servis çok yavaştı"   # Prompt'u deneyin
python -m yorumbot run         # DRY_RUN=true iken sadece gösterir, göndermez
```

Cevaplar beğenildiyse `.env` içinde `DRY_RUN=false` yapın:

```bash
python -m yorumbot run     # bir kez çalışır
python -m yorumbot watch   # sürekli açık kalır, POLL_SECONDS'da bir kontrol eder
```

`watch` yerine `run` komutunu cron / Windows Görev Zamanlayıcı ile örn. saatte bir çalıştırabilirsiniz.

## Prompt'u değiştirmek
Tüm cevap davranışı `prompt.txt` dosyasındadır: işletme adı, ton, iletişim numarası,
yasaklar vb. Dosyayı düzenlemeniz yeterli, kod değişikliği gerekmez.

## Ayarlar (`.env`)
| Ayar | Açıklama |
|---|---|
| `GEMINI_MODEL` | Varsayılan `gemini-flash-latest`. Liste: `python -m yorumbot models` |
| `DRY_RUN` | `true` ise cevaplar gönderilmez, sadece ekrana yazılır |
| `MIN_STARS` | Örn. `4` yaparsanız 1-3 yıldızlı yorumlar size bırakılır |
| `POLL_SECONDS` | `watch` modunda kontrol aralığı |

`.env`, `client_secret.json` ve `token.json` gizlidir; git'e eklenmez.
