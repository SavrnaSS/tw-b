import time
import os
import random
import re
import imaplib
import email.utils
import email
from seleniumwire import webdriver  # Using Selenium Wire for proxy authentication
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import email as email_module
from selenium.common.exceptions import TimeoutException
import pyttsx3
import undetected_chromedriver as uc


def notify_captcha():
        engine = pyttsx3.init()
        engine.say("2nd solve it!")
        engine.runAndWait()

# ---------------------------
# Gmail IMAP Config
# ---------------------------
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")  # Must match DESTINATION_EMAIL
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")  # Use an app password for Gmail
IMAP_SERVER = "imap.gmail.com"

# ---------------------------
# Proxy settings (Authenticated)
# ---------------------------
PROXY_HOST = "82.23.67.179"
PROXY_PORT = "5437"
PROXY_USER = "nftiuvfu"  # You can randomize or rotate if needed
PROXY_PASS = "8ris7fu5rgrn"
# Build the proxy URL with authentication
proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

# Selenium Wire proxy configuration
seleniumwire_options = {
    'proxy': {
        'http': proxy_url,
        'https': proxy_url,
        'no_proxy': 'localhost,127.0.0.1'
    }
}

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Headless Chrome + Selenium-Wire proxy + stealth tweaks."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")                  # true headless
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # override the UA to something realistic:
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )

    # your authenticated proxy
    proxy = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    seleniumwire_opts = {
        "proxy": {
            "http":  proxy,
            "https": proxy,
            "no_proxy": "localhost,127.0.0.1"
        }
    }

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
        seleniumwire_options=seleniumwire_opts
    )

    # minimal stealth: hide webdriver flag
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": 
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        }
    )

    return driver


# ---------------------------
# Utility Functions
# ---------------------------
def human_delay(a=2, b=6):
    """Sleep for a random duration between a and b seconds to mimic human behavior."""
    time.sleep(random.uniform(a, b))

def read_credentials(file_path="1st_step.txt"):
    """
    Reads credentials from a file and returns a list of dictionaries.
    Expected format:
    
    Email: example@domain.com
    Password: somepassword
    Username: someusername
    ----------------------------------------
    """
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
    """
    Logs into Twitter and handles additional verification steps.
    If an OTP confirmation page is detected, the function fetches the OTP from Gmail,
    enters it into the confirmation code input (using data-testid="ocfEnterTextTextInput"),
    and proceeds.
    """
    driver.get("https://twitter.com/login")
    wait = WebDriverWait(driver, 80)
    
    try:
        print("\n🔑 Logging into Twitter...")

        # 1. Fill email/username field
        email_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
        )
        email_field.clear()
        email_field.send_keys(user)
        print("✅ Entered email/username.")

        # 2. Click 'Next'
        next_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
        )
        next_btn.click()
        print("✅ Clicked 'Next'.")
        time.sleep(3)

        # 3. Check for additional verification prompt (phone/username)
        try:
            phone_or_username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']"))
            )
            phone_or_username_field.clear()
            phone_or_username_field.send_keys(user)
            print(f"✅ Re-entered username on verification page: {user}")

            next_button_2 = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
            )
            next_button_2.click()
            print("✅ Submitted phone/username verification.")
        except TimeoutException:
            print("✅ No additional verification prompt detected, continuing...")

        # 4. Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
        )
        password_field.clear()
        password_field.send_keys(twitter_password)
        print("✅ Entered password.")

        # 5. Click Log in
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Log in')]"))
        )
        login_btn.click()
        print("🎉 Login submitted!")
        time.sleep(5)
      
        # 6. Check if an OTP confirmation page is presented
        try:
            # Look for a message indicating that a confirmation code has been sent
            otp_prompt = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Check your email')]"))
            )
            print("📧 Email OTP prompt detected. Fetching OTP from Gmail...")
            otp = get_latest_otp_imap()
            if otp:
                # Locate the confirmation code input field using its data-testid
                otp_field = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")
                    )
                )
                otp_field.clear()
                otp_field.send_keys(otp)
                print("✅ Entered OTP into confirmation code input.")
                # Locate and click the Next button to submit the OTP
                submit_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]"))
                )
                submit_btn.click()
                print("✅ OTP submitted, continuing login flow.")
                time.sleep(5)
            else:
                print("❌ OTP was not retrieved from Gmail.")
        except TimeoutException:
            print("✅ No email OTP prompt detected; continuing normally.")

        # 7. Check for locked account prompt after OTP (if needed)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'locked')]"))
            )
            print("⚠️ Account appears to be locked. Initiating locked account flow...")
            if not handle_locked_account(driver):
                print("❌ Locked account flow failed.")
        except TimeoutException:
            print("✅ No locked account prompt detected; login flow complete.")

    except Exception as e:
        print(f"❌ Error during login flow: {e}")


def get_latest_otp_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
        mail.select("inbox")
        status, data = mail.search(
            None,
            'UNSEEN',
            'X-GM-RAW',
            '"newer_than:2m (confirmation code OR We noticed an attempt to log in OR \'one-time\')"'
        )
        if status != "OK":
            print("❌ IMAP search failed.")
            return None
        email_ids = data[0].split()
        if not email_ids:
            print("❌ No new OTP emails found via IMAP.")
            mail.logout()
            return None

        # Create a list to store (timestamp, email_id, message) tuples
        emails_with_dates = []
        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            if status != "OK":
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email_module.message_from_bytes(response_part[1])
                    date_tuple = email_module.utils.parsedate_tz(msg["Date"])
                    if date_tuple:
                        timestamp = email_module.utils.mktime_tz(date_tuple)
                        emails_with_dates.append((timestamp, e_id, msg))
        if not emails_with_dates:
            mail.logout()
            return None

        # Sort the list by timestamp (latest first)
        emails_with_dates.sort(key=lambda x: x[0], reverse=True)
        latest_timestamp, latest_email_id, latest_msg = emails_with_dates[0]

        # Extract the OTP from the email body
        body = ""
        if latest_msg.is_multipart():
            for part in latest_msg.walk():
                if part.get_content_type() == "text/plain" and part.get('Content-Disposition') is None:
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = latest_msg.get_payload(decode=True).decode(errors="ignore")
        
        print("----- RAW EMAIL BODY START -----")
        print(body[:500])
        print("----- RAW EMAIL BODY END -----")
        
        # Look for the phrase and capture the following code (6-12 alphanumeric characters)
        otp_match = re.search(
            r"by entering the following single-use code\.\s*([a-zA-Z0-9]{6,12})",
            body
        )

        if not otp_match:
            # Fallback: search for the first standalone 6-12 character alphanumeric code
            otp_match = re.search(r"\b([a-zA-Z0-9]{6,12})\b", body)

        if otp_match:
            otp = otp_match.group(1).strip()
            print(f"✅ OTP Found: {otp}")
            mail.store(latest_email_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
            return otp

        mail.logout()
        print("❌ OTP not found in the fetched email.")
        return None

    except Exception as e:
        print(f"❌ Error fetching OTP via IMAP: {e}")
        return None

def handle_locked_account(driver):
    """
    Handles the locked account flow:
      - Clicks the "Start" button,
      - Clicks the "Send email" button,
      - Waits briefly for the OTP email to arrive,
      - Extracts the OTP from email (via get_locked_otp()),
      - Enters the OTP in the token field and submits it.
      - After submission, checks for a captcha challenge; if found, alerts the user to solve it manually,
        and waits until the captcha is solved before proceeding.
    Returns True if successful, False otherwise.
    """
    wait = WebDriverWait(driver, 30)
    try:
        # Wait for a locked account message
        locked_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'locked')]"))
        )
        print("⚠️ Locked account detected, proceeding with verification flow.")
    except TimeoutException:
        print("✅ No locked account message found; skipping locked account flow.")
        return True

    try:
        # Click the "Start" or "Continue to X" button.
        start_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@type='submit' and contains(@class, 'EdgeButton--primary') and (@value='Start' or @value='Continue to X')]")
            )
        )
        start_btn.click()
        print("✅ Clicked 'Start' button.")
    except TimeoutException:
        print("❌ 'Start' button not found; cannot proceed with locked account flow.")
        return False

    try:
        # Click the 'Send email' button.
        send_email_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Send email']"))
        )
        send_email_btn.click()
        print("✅ Clicked 'Send email' button.")
    except TimeoutException:
        print("❌ 'Send email' button not found.")
        return False

    # Allow additional time for the OTP email to arrive
    time.sleep(10)  # Increased wait time for email to arrive

    # Retrieve the OTP from your email using the updated function with the correct subject filter
    otp = get_locked_otp(timeout=60, poll_interval=5, subject_filter="Confirm your email address")
    if not otp:
        print("❌ OTP not retrieved.")
        return False
    print(f"✅ OTP retrieved: {otp}")

    try:
        # Locate the OTP token input field and fill it
        token_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='token']"))
        )
        token_field.clear()
        token_field.send_keys(otp)
        print("✅ Entered OTP into token field.")
        token_field.submit()  # Alternatively, click a submit button if available
        print("✅ Submitted OTP.")
    except TimeoutException:
        print("❌ OTP token input field not found.")
        return False

    # Check for captcha challenge
    try:
        captcha_xpath = "//iframe[@id='arkose_iframe']"
         # Use a short timeout to quickly check if the captcha iframe is present
        captcha_wait = WebDriverWait(driver, 5)
        captcha_element = captcha_wait.until(
        EC.presence_of_element_located((By.XPATH, captcha_xpath))
        )
        if captcha_element:
            print("⚠️ Captcha challenge detected! Please solve the captcha manually.")
            notify_captcha()
            # Optionally, integrate text-to-speech here to alert you (e.g., using pyttsx3)
            # Wait until the captcha challenge is no longer active (i.e., solved manually)
            wait.until(EC.invisibility_of_element_located((By.XPATH, captcha_xpath)))
            # Instead of waiting for manual input, poll automatically until solved.
            wait_for_captcha_resolution(driver)
            print("✅ Captcha challenge solved.")

    except TimeoutException:
        print("✅ No captcha challenge detected, proceeding.")

    # Click on the "Continue to X" button
    try:
        time.sleep(5)
        continue_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@type='submit' and contains(@class, 'Button EdgeButton EdgeButton--primary') and @value='Continue to X']")
            )
        )
        continue_btn.click()
        print("✅ Clicked 'Continue to X' button.")
    except TimeoutException:
        print("❌ 'Continue to X' button not found.")
        return False

    # Continue with the next steps of your flow here...
    print("✅ Proceeding to the next step after verification.")
    return True
    

def get_locked_otp(timeout=30, poll_interval=5, subject_filter="Confirm your email address"):
    """
    Polls the Gmail inbox for a new OTP email for a given timeout period.
    Searches for unread emails with the specified subject.
    Returns the OTP if found, otherwise None.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(GMAIL_EMAIL, GMAIL_PASSWORD)
            mail.select("inbox")

            # Adjust the search criteria to match the expected subject
            status, data = mail.search(None, 'UNSEEN', f'SUBJECT "{subject_filter}"')
            if status != "OK":
                print("❌ IMAP search failed.")
                mail.logout()
                time.sleep(poll_interval)
                continue

            email_ids = data[0].split()
            if email_ids:
                # Process emails from newest to oldest
                for e_id in reversed(email_ids):
                    status, msg_data = mail.fetch(e_id, "(RFC822)")
                    if status != "OK":
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    body = ""
                    # Process all parts: check for both plain text and HTML content
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type in ["text/plain", "text/html"] and part.get('Content-Disposition') is None:
                                try:
                                    body += part.get_payload(decode=True).decode(errors="ignore")
                                except Exception as e:
                                    print(f"Error decoding part: {e}")
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception as e:
                            print(f"Error decoding email: {e}")

                    print("----- EMAIL CONTENT (first 500 chars) -----")
                    print(body.strip()[:500])
                    
                    # Adjust the regex as needed: here we assume OTP is a 6-digit number
                    otp_match = re.search(r'(\d{6})', body)
                    if otp_match:
                        otp = otp_match.group(1)
                        print(f"✅ OTP Found: {otp}")
                        mail.store(e_id, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        mail.logout()
                        return otp
            mail.logout()
        except Exception as e:
            print(f"❌ IMAP Error: {e}")
        # Wait before the next polling attempt
        time.sleep(poll_interval)
        time.sleep(5)
    print("❌ No OTP found after waiting.")
    return None


if __name__ == "__main__":
    creds = read_credentials("1st_step.txt")
    total_accounts = len(creds)
    print(f"📋 Found {total_accounts} credential sets.")

    account_count = 0  # Initialize the counter

    # Open the completed.txt file in append mode
    with open("completed.txt", "a") as completed_file:
        for cred in creds:
            account_count += 1  # Increment the counter
            user_email = cred.get("email")
            twitter_password = cred.get("password")
            user = cred.get("username")
            print(f"\n🚀 Processing account {account_count} of {total_accounts}: {user_email} | {user}")

            # Setup a new WebDriver instance for each account
            driver = setup_driver()
            driver.get("https://twitter.com/login")
            time.sleep(5)  # Allow time for the page to load

            try:
                login_twitter(driver, user_email, twitter_password, user)
                handle_locked_account(driver)
        
                 # If all actions are successful, write credentials to completed.txt
                with open('2nd_step.txt', 'a') as completed_file:
                  completed_file.write(f"{'Email:':<10} {user_email}\n")
                  completed_file.write(f"{'Password:':<10} {twitter_password}\n")
                  completed_file.write(f"{'Username:':<10} {user}\n")
                  completed_file.write(f"{'-' * 40}\n")
                print(f"✅ Successfully processed and recorded account: {user_email}")

                # Write the processed account's credentials to completed.txt
                completed_file.write(f"{user_email},{twitter_password},{user}\n")

            except Exception as e:
                print(f"❌ Error processing account {account_count} ({user_email}): {e}")

            finally:
                driver.quit()  # Close the browser instance
                print(f"🛑 Closed browser for account {account_count}: {user_email}")
                time.sleep(5)  # Pause before processing the next account

    print("🎉 All accounts processed.")
