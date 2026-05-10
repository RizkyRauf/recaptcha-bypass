"""
Test recaptcha_bypass on actual reCAPTCHA demo page
"""
from cloakbrowser import launch
from recaptcha_bypass import RecaptchaSolver

# Google reCAPTCHA demo
url = "https://www.google.com/recaptcha/api2/demo"
print(f"Testing on Google reCAPTCHA demo: {url}")
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
    
    if success:
        token = solver.get_token()
        print(f"Token: {token[:50]}..." if token else "No token")
else:
    print("No CAPTCHA detected")

page.wait_for_timeout(2000)
print(f"\nFinal title: {page.title()}")
page.screenshot(path="demo_test.png")

browser.close()
print("\n✅ Done!")
