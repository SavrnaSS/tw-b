import os
import re
import time
import random
import imaplib
from gtts import gTTS
from seleniumwire import webdriver  # For proxy support
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------
# Gmail IMAP Config (from .env)
# ---------------------------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

# ---------------------------
# Proxy Config (authenticated)
# ---------------------------
PROXY_HOST = "82.23.67.179"
PROXY_PORT = "5437"
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"
proxy_url = f"{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# ---------------------------
# Text-to-Speech Notifier
# ---------------------------
def notify_captcha():
    tts = gTTS("2nd solve it!")
    tts.save("/tmp/captcha.mp3")
    os.system("mpg123 /tmp/captcha.mp3")

# ---------------------------
# WebDriver Setup
# ---------------------------
def setup_driver():
    chrome_opts = webdriver.ChromeOptions()
    chrome_opts.add_argument("--headless=new")  # Remove 'new' if you face issues
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1920,1080")
    chrome_opts.add_argument("--disable-blink-features=AutomationControlled")
    chrome_opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )

    seleniumwire_opts = {
        "proxy": {
            "http": f"http://{proxy_url}",
            "https": f"https://{proxy_url}",
            "no_proxy": "localhost,127.0.0.1"
        }
    }

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_opts,
        seleniumwire_options=seleniumwire_opts
    )

    # Bypass navigator.webdriver flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )

    return driver

# ---------------------------
# Read Credentials
# ---------------------------
def read_credentials(path="1st_step.txt"):
    creds = []
    block = {}
    for line in open(path).read().splitlines():
        if not line.strip() or line.startswith("-"):
            if block:
                creds.append(block)
                block = {}
        else:
            k, v = line.split(":", 1)
            block[k.strip().lower()] = v.strip()
    if block:
        creds.append(block)
    return creds

# ---------------------------
# Fetch Latest OTP via IMAP
# ---------------------------
def get_latest_otp_imap():
    try:
        m = imaplib.IMAP4_SSL(IMAP_SERVER)
        m.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        m.select("inbox")
        _, data = m.search(None, 'UNSEEN', 'X-GM-RAW', '"confirmation code"')
        ids = data[0].split()
        if not ids:
            m.logout()
            return None
        latest = ids[-1]
        _, msg = m.fetch(latest, "(RFC822)")
        raw = msg[0][1].decode(errors="ignore")
        m.store(latest, '+FLAGS', '\\Deleted')
        m.expunge()
        m.logout()
        match = re.search(r"\b(\d{6})\b", raw)
        return match.group(1) if match else None
    except Exception:
        return None

# ---------------------------
# Login to Twitter
# ---------------------------
def login_twitter(driver, user, pwd):
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 30)

    # Email
    fld = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
    fld.clear()
    fld.send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()

    # Password
    fld = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']")))
    fld.clear()
    fld.send_keys(pwd)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))).click()

    # OTP Handling
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]")))
        otp = get_latest_otp_imap()
        if otp:
            fld = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")))
            fld.clear()
            fld.send_keys(otp)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
    except TimeoutException:
        pass

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == "__main__":
    creds = read_credentials()
    print(f"📋 Found {len(creds)} credential sets.")

    with open("2nd_step.txt", "a") as out:
        for idx, c in enumerate(creds, start=1):
            print(f"\n🚀 Processing {idx}/{len(creds)}: {c['email']}")
            driver = setup_driver()
            try:
                login_twitter(driver, c["email"], c["password"])
                out.write(
                    f"Email: {c['email']}\n"
                    f"Password: {c['password']}\n"
                    f"Username: {c['username']}\n"
                    + "-"*40 + "\n"
                )
                print("✅ Success")
            except Exception as e:
                print("❌ Failed:", e)
            finally:
                driver.quit()
                time.sleep(random.uniform(3, 6))

    print("🎉 All accounts processed.")
