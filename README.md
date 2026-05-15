# recaptcha-bypass

Selesaikan Google reCAPTCHA via audio challenge dalam waktu kurang dari 10 detik.

**Hanya bekerja dengan Playwright dan CloakBrowser.** Selenium WebDriver tidak didukung (lihat keterbatasan).

## Cara Kerja

Library ini beralih ke **audio challenge**, mengunduh file audio, mengonversinya ke WAV, dan menggunakan **Google Speech Recognition** untuk mentranskripsi angka/kata. Teks hasil transkripsi kemudian dimasukkan ke kolom respons.

## Instalasi

```bash
pip install recaptcha-bypass-RizkyRauf
```

Atau instal dari source:

```bash
git clone https://github.com/yourname/recaptcha-bypass.git
cd recaptcha-bypass
pip install -e .
```

**Dependensi:**
- `pydub` - konversi audio (membutuhkan `ffmpeg`: `sudo apt install ffmpeg`)
- `SpeechRecognition` - speech-to-text

## Quick Start

### Dengan CloakBrowser

```python
from cloakbrowser import launch
from recaptcha_bypass import RecaptchaSolver

browser = launch(headless=True, humanize=True)
page = browser.new_page()
page.goto("https://protected-site.com")

solver = RecaptchaSolver(page)
solver.solve_captcha()

print(page.title())
browser.close()
```

### Dengan Playwright

```python
from playwright.sync_api import sync_playwright
from recaptcha_bypass import RecaptchaSolver

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://protected-site.com")

    solver = RecaptchaSolver(page)
    solver.solve_captcha()

    print(page.title())
    browser.close()
```

### Dengan SeleniumBase (CDP Mode) — tanpa package ini

Package ini **tidak support Selenium atau SeleniumBase**. Tapi SeleniumBase UC+CDP mode bisa bypass reCAPTCHA langsung:

```python
from seleniumbase import SB

with SB(uc=True, test=True, headless=True) as sb:
    sb.activate_cdp_mode("https://protected-site.com")
    sb.sleep(3)

    # SeleniumBase CDP mode otomatis handle reCAPTCHA
    print(sb.get_title())
```

## API

### `RecaptchaSolver(driver, *, headless=True)`

| Parameter | Tipe | Default | Deskripsi |
|---|---|---|---|
| `driver` | Playwright Page / CloakBrowser Page | required | Driver browser automation |
| `headless` | bool | `True` | Apakah browser berjalan headless |

### Methods

| Method | Return | Deskripsi |
|---|---|---|
| `solve_captcha(max_retries=5)` | `bool` | Selesaikan reCAPTCHA di halaman saat ini |
| `is_solved()` | `bool` | Cek apakah reCAPTCHA sudah terpecahkan |
| `is_detected()` | `bool` | Cek apakah bot terdeteksi |
| `get_token()` | `str \| None` | Dapatkan token respons reCAPTCHA |

## Advanced Usage

### Retry dengan custom attempts

```python
solver = RecaptchaSolver(page)
success = solver.solve_captcha(max_retries=10)
if not success:
    print("Gagal menyelesaikan CAPTCHA")
```

### Cek apakah CAPTCHA ada sebelum menyelesaikan

```python
solver = RecaptchaSolver(page)
if solver._has_recaptcha():
    print("CAPTCHA terdeteksi, menyelesaikan...")
    solver.solve_captcha()
else:
    print("Tidak ada CAPTCHA")
```

### Dapatkan token reCAPTCHA untuk panggilan API

```python
solver = RecaptchaSolver(page)
solver.solve_captcha()
token = solver.get_token()
if token:
    print(f"Token reCAPTCHA: {token[:50]}...")
```

## Situs yang Didukung

| Situs | Tipe CAPTCHA | Tingkat Keberhasilan |
|---|---|---|
| radaronline.id | reCAPTCHA v2 | ✅ Tinggi |
| GitLab login | reCAPTCHA v2 | ✅ Tinggi |
| Ahrefs | reCAPTCHA v2 | ✅ Tinggi |
| Situs reCAPTCHA v2 lainnya | reCAPTCHA v2 | ✅ Tinggi |

## Keterbatasan

- **reCAPTCHA v2 only** - tidak mendukung reCAPTCHA v3, Enterprise, atau hCaptcha
- **Selenium WebDriver TIDAK didukung** - Chrome security restriction mencegah Selenium berinteraksi dengan iframe cross-origin. Gunakan Playwright atau CloakBrowser.
- **Rate limiting** - Google dapat memblokir IP jika terlalu banyak CAPTCHA diselesaikan dalam waktu cepat. Gunakan proxy atau tambahkan delay.
- **Audio recognition** - tergantung akurasi Google Speech API. Mungkin gagal pada audio yang bising.
- **Bukan untuk skala produksi** - untuk scraping skala besar, pertimbangkan layanan CAPTCHA solving berbayar (CapSolver, 2Captcha).

## Arsitektur

```
┌─────────────────────────────────────────────────┐
│                 recaptcha-bypass                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────┐                        │
│  │  Playwright           │                        │
│  │  (CloakBrowser)       │  ✅ Berfungsi penuh    │
│  └──────────┬───────────┘                        │
│             │                                    │
│  ┌──────────▼───────────┐                        │
│  │    RecaptchaSolver     │                        │
│  │                        │                        │
│  │  1. Click checkbox     │                        │
│  │  2. Switch to audio    │                        │
│  │  3. Download MP3       │                        │
│  │  4. Convert to WAV     │                        │
│  │  5. Speech → Text      │                        │
│  │  6. Submit answer      │                        │
│  │  7. Retry if needed    │                        │
│  └────────────────────────┘                        │
│             │                                    │
│  ┌──────────▼───────────┐                        │
│  │   pydub +             │                        │
│  │   SpeechRecognition   │                        │
│  └───────────────────────┘                        │
│                                                  │
│  Catatan: Selenium ❌ Tidak didukung              │
│  (cross-origin iframe restriction)                │
└─────────────────────────────────────────────────┘
```

## Lisensi

MIT
