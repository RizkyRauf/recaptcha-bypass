# recaptcha-bypass

Solve Google reCAPTCHA via audio challenge in less than 10 seconds. 🚀

Works with **Playwright**, **CloakBrowser**, and **Selenium** drivers.

## How It Works

Instead of solving the image captcha, this library switches to the **audio challenge**, downloads the audio file, converts it to WAV, and uses **Google Speech Recognition** to transcribe the numbers/words. The transcribed text is then entered into the response field.

## Installation

```bash
pip install recaptcha-bypass-RizkyRauf
```

Or install from source:

```bash
git clone https://github.com/yourname/recaptcha-bypass.git
cd recaptcha-bypass
pip install -e .
```

**Dependencies:**
- `pydub` - audio conversion (requires `ffmpeg`: `sudo apt install ffmpeg`)
- `SpeechRecognition` - speech-to-text

## Quick Start

### With CloakBrowser

```python
from cloakbrowser import launch
from recaptcha_bypass import RecaptchaSolver

browser = launch(headless=True, humanize=True)
page = browser.new_page()
page.goto("https://protected-site.com")

solver = RecaptchaSolver(page)
solver.solve_captcha()

# Page is now accessible
print(page.title())
browser.close()
```

### With Playwright

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

### With Selenium

```python
from selenium import webdriver
from recaptcha_bypass import RecaptchaSolver

driver = webdriver.Chrome()
driver.get("https://www.google.com/recaptcha/api2/demo")

solver = RecaptchaSolver(driver)
solver.solve_captcha()

print(driver.title)
driver.quit()
```

### With SeleniumBase

```python
from seleniumbase import SB
from recaptcha_bypass import RecaptchaSolver

with SB(uc=True, headless=True) as sb:
    sb.open("https://protected-site.com")
    sb.sleep(5)

    solver = RecaptchaSolver(sb.driver)
    solver.solve_captcha()

    print(sb.get_title())
```

## API

### `RecaptchaSolver(driver, *, headless=True)`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `driver` | Playwright Page / Selenium WebDriver | required | Browser automation driver |
| `headless` | bool | `True` | Whether browser runs headless |

### Methods

| Method | Returns | Description |
|---|---|---|
| `solve_captcha(max_retries=5)` | `bool` | Solve reCAPTCHA on current page |
| `is_solved()` | `bool` | Check if reCAPTCHA is solved |
| `is_detected()` | `bool` | Check if bot was detected |
| `get_token()` | `str \| None` | Get reCAPTCHA response token |

## Advanced Usage

### Retry with custom attempts

```python
solver = RecaptchaSolver(page)
success = solver.solve_captcha(max_retries=10)
if not success:
    print("Failed to solve CAPTCHA")
```

### Check if CAPTCHA exists before solving

```python
solver = RecaptchaSolver(page)
if solver._has_recaptcha():
    print("CAPTCHA detected, solving...")
    solver.solve_captcha()
else:
    print("No CAPTCHA found")
```

### Get reCAPTCHA token for API calls

```python
solver = RecaptchaSolver(page)
solver.solve_captcha()
token = solver.get_token()
if token:
    # Use token in your API request
    print(f"reCAPTCHA token: {token[:50]}...")
```

### Combined with CloakBrowser stealth

```python
from cloakbrowser import launch
from recaptcha_bypass import RecaptchaSolver

# CloakBrowser prevents CAPTCHA from appearing (~80% cases)
browser = launch(headless=True, humanize=True)
page = browser.new_page()
page.goto("https://protected-site.com")

# Fallback: solve CAPTCHA if it still appears
solver = RecaptchaSolver(page)
if solver._has_recaptcha():
    solver.solve_captcha()

# Now scrape
content = page.inner_text("body")
browser.close()
```

## Supported Sites

| Site | CAPTCHA Type | Success Rate |
|---|---|---|
| radaronline.id | reCAPTCHA v2 | ✅ High |
| GitLab login | reCAPTCHA v2 | ✅ High |
| Ahrefs | reCAPTCHA v2 | ✅ High |
| Any reCAPTCHA v2 site | reCAPTCHA v2 | ✅ High |

## Limitations

- **reCAPTCHA v2 only** - does not support reCAPTCHA v3, Enterprise, or hCaptcha
- **Rate limiting** - Google may block your IP if you solve too many CAPTCHAs quickly. Use proxies or add delays between solves
- **Audio recognition** - depends on Google Speech API accuracy. May fail on noisy audio
- **Not for production scale** - for large-scale scraping, consider paid CAPTCHA solving services (CapSolver, 2Captcha)

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 recaptcha-bypass                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐    ┌──────────────────────┐   │
│  │  Playwright   │    │      Selenium         │   │
│  │  (CloakBrowser)│    │   (WebDriver)         │   │
│  └──────┬───────┘    └──────────┬───────────┘   │
│         │                       │                │
│         └───────────┬───────────┘                │
│                     │                            │
│         ┌───────────▼───────────┐                │
│         │    RecaptchaSolver     │                │
│         │                        │                │
│         │  1. Click checkbox     │                │
│         │  2. Switch to audio    │                │
│         │  3. Download MP3       │                │
│         │  4. Convert to WAV     │                │
│         │  5. Speech → Text      │                │
│         │  6. Submit answer      │                │
│         │  7. Retry if needed    │                │
│         └────────────────────────┘                │
│                     │                            │
│         ┌───────────▼───────────┐                │
│         │   pydub +             │                │
│         │   SpeechRecognition   │                │
│         └───────────────────────┘                │
└─────────────────────────────────────────────────┘
```

## License

MIT
