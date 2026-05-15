"""
Google reCAPTCHA solver via audio challenge.
Works with Playwright (CloakBrowser) and Selenium drivers.
"""
import os
import random
import time
import urllib.request
from typing import Optional

import pydub
import speech_recognition


class RecaptchaSolver:
    """Solve Google reCAPTCHA via audio challenge.

    Supports:
        - Playwright Page (CloakBrowser, Playwright)
        - Selenium WebDriver
        - SeleniumBase SB driver

    Usage with CloakBrowser:
        from cloakbrowser import launch
        from recaptcha_bypass import RecaptchaSolver

        browser = launch(headless=True)
        page = browser.new_page()
        page.goto("https://protected-site.com")

        solver = RecaptchaSolver(page)
        solver.solve_captcha()

    Usage with Selenium:
        from selenium import webdriver
        from recaptcha_bypass import RecaptchaSolver

        driver = webdriver.Chrome()
        solver = RecaptchaSolver(driver)
        solver.solve_captcha()
    """

    TIMEOUT_STANDARD = 10
    TIMEOUT_SHORT = 2
    MAX_RETRIES = 5

    def __init__(self, driver, *, headless: bool = True):
        """Initialize solver.

        Args:
            driver: Playwright Page, Selenium WebDriver, or CloakBrowser page
            headless: Whether browser is headless (affects click strategy)
        """
        self.driver = driver
        self.headless = headless
        self._driver_type = self._detect_driver_type()

    def _detect_driver_type(self) -> str:
        """Detect whether driver is Playwright or Selenium."""
        driver_cls = type(self.driver).__name__
        if "Page" in driver_cls or "page" in driver_cls.lower():
            return "playwright"
        return "selenium"

    def solve_captcha(self, *, max_retries: int = MAX_RETRIES) -> bool:
        """Solve reCAPTCHA on current page.

        Args:
            max_retries: Maximum audio challenge retry attempts

        Returns:
            True if solved, False if not

        Raises:
            Exception: If bot detected
        """
        if not self._has_recaptcha():
            return True

        # Click checkbox
        self._click_checkbox()
        time.sleep(2)

        if self.is_solved():
            return True

        # Switch to audio challenge
        self._click_audio_button()
        time.sleep(3)

        if self.is_detected():
            raise Exception("Bot detected by reCAPTCHA")

        # Solve audio challenge with retries
        for attempt in range(max_retries):
            audio_url = self._get_audio_url()
            if not audio_url:
                continue

            try:
                text = self._process_audio(audio_url)
                self._submit_answer(text)
                time.sleep(3)

                if self.is_solved():
                    return True

                # Reload for new audio
                self._reload_audio()
                time.sleep(2)

            except Exception:
                continue

        return False

    def _has_recaptcha(self) -> bool:
        """Check if reCAPTCHA is present on page."""
        if self._driver_type == "playwright":
            return len(self.driver.frames) > 0 and any(
                "recaptcha" in f.url.lower() for f in self.driver.frames
            )
        else:
            try:
                self.driver.switch_to.default_content()
                frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
                return len(frames) > 0
            except Exception:
                return False

    def _click_checkbox(self):
        """Click the reCAPTCHA checkbox."""
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower() and "anchor" in f.url:
                    checkbox = f.query_selector("#recaptcha-anchor, [role='checkbox']")
                    if checkbox:
                        checkbox.click()
                        return
                    container = f.query_selector("#rc-anchor-container")
                    if container:
                        container.click()
                        return
        else:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            for frame in frames:
                self.driver.switch_to.frame(frame)
                checkbox = self.driver.find_elements("xpath", "//*[@role='checkbox']")
                if checkbox:
                    checkbox[0].click()
                    self.driver.switch_to.default_content()
                    return
                container = self.driver.find_elements("xpath", "//*[@id='rc-anchor-container']")
                if container:
                    container[0].click()
                    self.driver.switch_to.default_content()
                    return
                self.driver.switch_to.default_content()

    def _click_audio_button(self):
        """Click the audio challenge button."""
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower():
                    for selector in [
                        "#recaptcha-audio-button",
                        "button[title*='audio']",
                        ".rc-button-audio",
                        "[aria-label*='audio']",
                    ]:
                        btn = f.query_selector(selector)
                        if btn and btn.is_visible():
                            btn.click()
                            return
        else:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            for frame in frames:
                self.driver.switch_to.frame(frame)
                btn = self.driver.find_elements("xpath", "//*[@id='recaptcha-audio-button']")
                if btn:
                    btn[0].click()
                    self.driver.switch_to.default_content()
                    return
                self.driver.switch_to.default_content()

    def _get_audio_url(self) -> Optional[str]:
        """Extract audio URL from reCAPTCHA frame."""
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower():
                    try:
                        audio_el = f.query_selector("audio")
                        if audio_el:
                            return audio_el.get_attribute("src")
                        source = f.query_selector("#audio-source")
                        if source:
                            return source.get_attribute("src")
                    except Exception:
                        pass
        else:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            for frame in frames:
                self.driver.switch_to.frame(frame)
                try:
                    audio = self.driver.find_elements("xpath", "//audio")
                    if audio:
                        return audio[0].get_attribute("src")
                    source = self.driver.find_elements("xpath", "//*[@id='audio-source']")
                    if source:
                        return source[0].get_attribute("src")
                except Exception:
                    pass
                self.driver.switch_to.default_content()
        return None

    def _process_audio(self, audio_url: str) -> str:
        """Download audio, convert to WAV, recognize speech.

        Args:
            audio_url: URL of reCAPTCHA audio file

        Returns:
            Recognized text string
        """
        temp_dir = os.getenv("TEMP") if os.name == "nt" else "/tmp"
        mp3_path = os.path.join(temp_dir, f"recaptcha_{random.randrange(1, 10000)}.mp3")
        wav_path = os.path.join(temp_dir, f"recaptcha_{random.randrange(1, 10000)}.wav")

        try:
            urllib.request.urlretrieve(audio_url, mp3_path)
            sound = pydub.AudioSegment.from_mp3(mp3_path)
            sound.export(wav_path, format="wav")

            recognizer = speech_recognition.Recognizer()
            with speech_recognition.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)

            return recognizer.recognize_google(audio_data)

        finally:
            for path in (mp3_path, wav_path):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

    def _submit_answer(self, text: str):
        """Enter recognized text and press Enter."""
        answer = text.lower().replace(" ", "")
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower():
                    response_input = f.query_selector("#audio-response")
                    if response_input and response_input.is_visible():
                        response_input.click()
                        time.sleep(0.3)
                        response_input.fill(answer)
                        time.sleep(0.3)
                        response_input.press("Enter")
                        return
        else:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            for frame in frames:
                self.driver.switch_to.frame(frame)
                response = self.driver.find_elements("xpath", "//*[@id='audio-response']")
                if response:
                    response[0].clear()
                    response[0].send_keys(answer)
                    time.sleep(0.3)
                    response[0].send_keys("\n")
                    self.driver.switch_to.default_content()
                    return
                self.driver.switch_to.default_content()

    def _reload_audio(self):
        """Click reload button for new audio challenge."""
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower():
                    try:
                        btn = f.query_selector("#recaptcha-reload-button")
                        if btn and btn.is_visible():
                            btn.click()
                            return
                    except Exception:
                        pass
        else:
            self.driver.switch_to.default_content()
            frames = self.driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            for frame in frames:
                self.driver.switch_to.frame(frame)
                btn = self.driver.find_elements("xpath", "//*[@id='recaptcha-reload-button']")
                if btn:
                    btn[0].click()
                    self.driver.switch_to.default_content()
                    return
                self.driver.switch_to.default_content()

    def is_solved(self) -> bool:
        """Check if reCAPTCHA is solved."""
        if self._driver_type == "playwright":
            title = self.driver.title()
            if "Bot Verification" in title or "Just a moment" in title:
                return False
            return True
        else:
            try:
                checkmark = self.driver.find_elements(
                    "xpath", "//*[@class='recaptcha-checkbox-checkmark']"
                )
                if checkmark:
                    style = checkmark[0].get_attribute("style")
                    return style is not None and len(style) > 0
            except Exception:
                pass
            return False

    def is_detected(self) -> bool:
        """Check if bot was detected."""
        if self._driver_type == "playwright":
            try:
                body = self.driver.inner_text("body")
                return "Try again later" in body or "excessive traffic" in body.lower()
            except Exception:
                return False
        else:
            try:
                body = self.driver.find_element("xpath", "//body").text
                return "Try again later" in body or "excessive traffic" in body.lower()
            except Exception:
                return False

    def get_token(self) -> Optional[str]:
        """Get reCAPTCHA response token."""
        if self._driver_type == "playwright":
            for f in self.driver.frames:
                if "recaptcha" in f.url.lower():
                    try:
                        token = f.query_selector("#recaptcha-token")
                        if token:
                            return token.get_attribute("value")
                    except Exception:
                        pass
        else:
            try:
                token = self.driver.find_element("xpath", "//*[@id='recaptcha-token']")
                return token.get_attribute("value")
            except Exception:
                pass
        return None
