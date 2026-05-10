"""
Test recaptcha_bypass package with CloakBrowser
"""
from cloakbrowser import launch
from recaptcha_bypass import RecaptchaSolver

url = "https://radaronline.id"
print(f"Testing recaptcha-bypass on {url}")
print("=" * 50)

browser = launch(headless=True, humanize=True)
page = browser.new_page()

print("Navigating...")
page.goto(url, wait_until="domcontentloaded", timeout=20000)
page.wait_for_timeout(5000)

title = page.title()
print(f"Title: {title}")

solver = RecaptchaSolver(page)

if solver._has_recaptcha():
    print("CAPTCHA detected, solving...")
    success = solver.solve_captcha()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
else:
    print("No CAPTCHA - CloakBrowser stealth worked!")

# Verify access
page.wait_for_timeout(2000)
print(f"\nFinal title: {page.title()}")
body = page.inner_text("body")
print(f"Content: {body[:150]}...")

browser.close()
print("\n✅ Done!")
