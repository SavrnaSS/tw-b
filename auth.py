import time
import os
import random
import re
import imaplib
import email as email_module

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from gtts import gTTS

# ---------------------------
# Config
# ---------------------------
GMAIL_EMAIL    = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
IMAP_SERVER    = "imap.gmail.com"

PROXY_HOST = "82.23.67.179"
PROXY_PORT = "5437"
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"

def notify_captcha():
    tts = gTTS("Please solve the captcha now")
    tts.save("captcha.mp3")
    os.system("mpg123 captcha.mp3")

def setup_driver():
    # 1) ChromeOptions
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"        # ensure Chromium is installed
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
    # proxy
    options.add_argument(
        f"--proxy-server=http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    )

    # 2) download/install matching chromedriver
    driver_path = ChromeDriverManager().install()

    # 3) launch undetected-chromedriver
    driver = uc.Chrome(
        options=options,
        driver_executable_path=driver_path,
        browser_executable_path="/usr/bin/chromium-browser"
    )

    # stealth
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )
    return driver

def wait_for_captcha_resolution(driver, timeout=300):
    xpath = "//iframe[@id='arkose_iframe']"
    start = time.time()
    alerted = False
    while time.time() - start < timeout:
        try:
            driver.find_element(By.XPATH, xpath)
            if not alerted:
                print("⚠️ Captcha detected. Alerting user.")
                notify_captcha()
                alerted = True
            time.sleep(5)
        except:
            return True
    print("⚠️ Captcha not solved in time.")
    return False

def human_delay(a=2, b=6):
    time.sleep(random.uniform(a, b))

def read_credentials(path="1st_step.txt"):
    creds, block = [], {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("-"):
                if block:
                    creds.append(block)
                    block = {}
            else:
                k, v = line.split(":", 1)
                block[k.lower().strip()] = v.strip()
    if block:
        creds.append(block)
    return creds

def get_latest_otp_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW', '"newer_than:2m confirmation code"')
        if status != "OK" or not data[0]:
            return None
        ids = data[0].split()
        msgs = []
        for eid in ids:
            _, md = mail.fetch(eid, "(RFC822)")
            msg = email_module.message_from_bytes(md[0][1])
            dt = email_module.utils.parsedate_tz(msg["Date"])
            ts = email_module.utils.mktime_tz(dt) if dt else 0
            msgs.append((ts, msg))
        msgs.sort(reverse=True)
        body = ""
        m = msgs[0][1]
        if m.is_multipart():
            for part in m.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = m.get_payload(decode=True).decode(errors="ignore")
        match = re.search(r"\b(\d{6,12})\b", body)
        return match.group(1) if match else None
    except Exception as e:
        print(f"IMAP error: {e}")
        return None

def handle_locked_account(driver):
    try:
        wait = WebDriverWait(driver, 30)
        cont = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Continue')]")))
        cont.click()
        email_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Email')]")))
        email_btn.click()

        otp = None
        for _ in range(6):
            time.sleep(10)
            otp = get_latest_otp_imap()
            if otp:
                print(f"✅ OTP retrieved: {otp}")
                break
        if not otp:
            print("❌ Failed to retrieve OTP.")
            return False

        otp_in = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")))
        otp_in.send_keys(otp)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))).click()
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Locked-account error: {e}")
        return False

def login_twitter(driver, user, pwd):
    wait = WebDriverWait(driver, 60)
    driver.get("https://twitter.com/login")
    u = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
    u.send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
    time.sleep(2)

    p = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']")))
    p.send_keys(pwd)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))).click()
    time.sleep(5)

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]")))
        otp = get_latest_otp_imap()
        if otp:
            inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")))
            inp.send_keys(otp)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
            time.sleep(5)
    except TimeoutException:
        pass

    try:
        if driver.find_elements(By.XPATH, "//*[contains(text(),'locked')]"):
            handle_locked_account(driver)
    except:
        pass

def main():
    creds = read_credentials("1st_step.txt")
    print(f"📋 Found {len(creds)} accounts.")
    with open("completed.txt", "a") as done:
        for i, c in enumerate(creds, start=1):
            email = c.get("email"); pwd = c.get("password"); user = c.get("username")
            print(f"\n=== [{i}/{len(creds)}] {email} ===")
            driver = setup_driver()
            try:
                login_twitter(driver, user, pwd)
                done.write(f"{email},{pwd},{user}\n")
                print("✅ Success")
            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                driver.quit()
                time.sleep(5)

if __name__ == "__main__":
    main()
