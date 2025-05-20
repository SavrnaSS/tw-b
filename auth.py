import time
import os
import random
import re
import imaplib
import email as email_module
from seleniumwire import webdriver  # proxy support
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
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
PROXY_URL  = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
SW_OPTIONS = {
    'proxy': {
        'http':  PROXY_URL,
        'https': PROXY_URL,
        'no_proxy': 'localhost,127.0.0.1'
    }
}

def notify_captcha():
    tts = gTTS("Please solve the captcha now")
    tts.save("captcha.mp3")
    os.system("mpg123 captcha.mp3")

def setup_driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
    # use system Chromium on Render
    opts.binary_location = "/usr/bin/chromium-browser"

    try:
        # Try undetected-chromedriver
        return uc.Chrome(
            options=opts,
            seleniumwire_options=SW_OPTIONS,
            driver_executable_path="/usr/bin/chromedriver",
            headless=True
        )
    except Exception as e:
        print(f"undetected-chromedriver failed: {e}\nFalling back to selenium-wire ChromeDriver")
        return webdriver.Chrome(
            service=Service("/usr/bin/chromedriver"),
            options=opts,
            seleniumwire_options=SW_OPTIONS
        )

def wait_for_captcha_resolution(driver, timeout=300):
    xpath = "//iframe[@id='arkose_iframe']"
    start = time.time()
    notified = False
    while time.time() - start < timeout:
        try:
            driver.find_element(By.XPATH, xpath)
            if not notified:
                print("⚠️ Captcha detected. Alerting user.")
                notify_captcha()
                notified = True
            time.sleep(5)
        except:
            return True
    return False

def read_credentials(path="1st_step.txt"):
    creds, block = [], {}
    for line in open(path, "r", encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("---"):
            if block:
                creds.append(block)
                block = {}
        else:
            k, v = line.split(":",1)
            block[k.strip().lower()] = v.strip()
    if block: creds.append(block)
    return creds

def get_latest_otp_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW', '"newer_than:2m confirmation code"')
        if status != "OK": return None
        ids = data[0].split()
        if not ids: return None

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
                if part.get_content_type()=="text/plain":
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
            if otp: break
        if not otp: return False

        otp_in = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")))
        otp_in.send_keys(otp)
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]")))
        next_btn.click()
        time.sleep(5)
        return True
    except Exception as e:
        print(f"Locked-account flow error: {e}")
        return False

def login_twitter(driver, user, pwd):
    wait = WebDriverWait(driver, 60)
    driver.get("https://twitter.com/login")
    # username
    u = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='text']")))
    u.send_keys(user)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()
    time.sleep(2)
    # password
    p = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']")))
    p.send_keys(pwd)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))).click()
    time.sleep(5)
    # OTP?
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
    # locked?
    try:
        if driver.find_elements(By.XPATH, "//*[contains(text(),'locked')]"):
            handle_locked_account(driver)
    except:
        pass

def main():
    creds = read_credentials("1st_step.txt")
    print(f"📋 Found {len(creds)} accounts.")
    with open("completed.txt","a") as done:
        for i, c in enumerate(creds,1):
            e = c.get("email"); p = c.get("password"); u = c.get("username")
            print(f"\n=== [{i}/{len(creds)}] {e} ===")
            driver = setup_driver()
            try:
                login_twitter(driver, u, p)
                # mark success
                done.write(f"{e},{p},{u}\n")
                print("✅ Done")
            except Exception as ex:
                print(f"❌ Error: {ex}")
            finally:
                driver.quit()
                time.sleep(5)

if __name__ == "__main__":
    main()
