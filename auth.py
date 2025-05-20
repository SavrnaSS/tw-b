import time
import os
import random
import re
import imaplib
import email
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import logging
from gtts import gTTS

# Set up logging
logging.basicConfig(level=logging.INFO)

# Audio notification for captcha
def notify_captcha():
    tts = gTTS("Please solve the captcha!")
    tts.save("captcha.mp3")
    os.system("mpg123 captcha.mp3")

# Gmail IMAP Configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

# Proxy Configuration
PROXY_HOST = "82.23.67.179"
PROXY_PORT = "5437"
PROXY_USER = "nftiuvfu"
PROXY_PASS = "8ris7fu5rgrn"
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
seleniumwire_options = {
    'proxy': {
        'http': proxy_url,
        'https': proxy_url,
        'no_proxy': 'localhost,127.0.0.1'
    }
}

def setup_driver():
    """Set up headless Chrome with proxy and stealth settings."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    chrome_options.binary_location = "/usr/bin/google-chrome"

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
        )
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def human_delay(a=2, b=6):
    """Random delay to mimic human behavior."""
    time.sleep(random.uniform(a, b))

def read_credentials(file_path="1st_step.txt"):
    """Read credentials from a file."""
    credentials = []
    with open(file_path, "r") as f:
        lines = f.read().splitlines()
    block = {}
    for line in lines:
        if not line.strip() or line.startswith("-"):
            if block:
                credentials.append(block)
                block = {}
        else:
            if line.startswith("Email:"):
                block["email"] = line.split("Email:")[1].strip()
            elif line.startswith("Password:"):
                block["password"] = line.split("Password:")[1].strip()
            elif line.startswith("Username:"):
                block["username"] = line.split("Username:")[1].strip()
    if block:
        credentials.append(block)
    return credentials

def login_twitter(driver, email, twitter_password, user):
    """Log into Twitter with OTP and locked account handling."""
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 80)

    try:
        logging.info("Logging into Twitter...")

        # Enter email/username
        email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']")))
        email_field.send_keys(user)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))).click()
        human_delay()

        # Handle additional verification (if prompted)
        try:
            phone_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")))
            phone_field.send_keys(user)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))).click()
        except TimeoutException:
            logging.info("No additional verification required.")

        # Enter password
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']")))
        password_field.send_keys(twitter_password)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]"))).click()
        human_delay(3, 5)

        # Handle OTP (if prompted)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]")))
            logging.info("OTP required. Fetching from Gmail...")
            otp = get_latest_otp_imap()
            if otp:
                otp_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")))
                otp_field.send_keys(otp)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))).click()
            else:
                logging.error("OTP not retrieved.")
        except TimeoutException:
            logging.info("No OTP required.")

    except Exception as e:
        logging.error(f"Login error: {e}")

def get_latest_otp_imap():
    """Fetch the latest OTP from Gmail."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(None, 'UNSEEN', 'X-GM-RAW', '"confirmation code"')
        if status != "OK" or not data[0]:
            logging.error("No OTP emails found.")
            mail.logout()
            return None

        email_ids = data[0].split()
        status, msg_data = mail.fetch(email_ids[-1], "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        body = msg.get_payload(decode=True).decode(errors="ignore") if not msg.is_multipart() else "".join(
            part.get_payload(decode=True).decode(errors="ignore") for part in msg.walk() if part.get_content_type() == "text/plain"
        )

        otp_match = re.search(r"\b(\d{6})\b", body)
        if otp_match:
            otp = otp_match.group(1)
            logging.info(f"OTP Found: {otp}")
            mail.logout()
            return otp
        mail.logout()
        return None
    except Exception as e:
        logging.error(f"OTP fetch error: {e}")
        return None

if __name__ == "__main__":
    creds = read_credentials()
    logging.info(f"Found {len(creds)} accounts.")

    for i, cred in enumerate(creds, 1):
        email, password, username = cred["email"], cred["password"], cred["username"]
        logging.info(f"Processing account {i}/{len(creds)}: {email}")

        driver = setup_driver()
        try:
            login_twitter(driver, email, password, username)
            with open("completed.txt", "a") as f:
                f.write(f"{email},{password},{username}\n")
            logging.info(f"Account {email} processed successfully.")
        except Exception as e:
            logging.error(f"Error with {email}: {e}")
        finally:
            driver.quit()
            human_delay()
    logging.info("All accounts processed.")