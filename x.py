from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from datetime import datetime
from retrying import retry
import imaplib
import email
import re

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7496191174:AAHEvWNlToVLEPkKLAjfWkjsmiTI0igEhnM"
# TELEGRAM_CHANNEL_ID = '-1002466361480'  # Should start with @ for public channels
TELEGRAM_CHANNEL_ID = "@alfabootie"


def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML",  # Enables HTML formatting
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")


def get_verification_code_from_gmail(gmail_email, gmail_password):
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Login to Gmail
        mail.login(gmail_email, gmail_password)
        mail.select("inbox")
        
        # Search for recent emails from Twitter/X
        _, messages = mail.search(None, '(FROM "info@x.com" UNSEEN)')
        email_ids = messages[0].split()
        
        if not email_ids:
            return None
            
        # Get the latest email
        latest_email_id = email_ids[-1]
        _, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        email_body = msg_data[0][1]
        message = email.message_from_bytes(email_body)
        
        # Extract verification code - looking for 8 character alphanumeric code
        code = None
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    # Look for an 8-character code that appears alone on a line
                    match = re.search(r'^([a-z0-9]{8})\s*$', body, re.MULTILINE)
                    if match:
                        code = match.group(1)
                        break
        else:
            body = message.get_payload(decode=True).decode()
            match = re.search(r'^([a-z0-9]{8})\s*$', body, re.MULTILINE)
            if match:
                code = match.group(1)
        
        mail.logout()
        return code
        
    except Exception as e:
        print(f"Error getting verification code: {e}")
        send_telegram_message(f"❌ Error getting verification code: {e}")
        return None


def login_to_twitter(driver, your_email, your_password, gmail_password):
    try:
        driver.get("https://twitter.com/i/flow/login")
        time.sleep(3)

        # Step 1: Enter email
        email_field = driver.find_element(By.XPATH, "//input[@autocomplete='username']")
        email_field.send_keys(your_email)
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        time.sleep(3)

        # Step 2: Handle unusual activity check (email verification)
        try:
            verify_email = driver.find_element(
                By.XPATH, "//input[@autocomplete='email']"
            )
            if verify_email:
                print("Email verification required")
                send_telegram_message("📧 Email verification required")
                verify_email.send_keys(your_email)
                driver.find_element(By.XPATH, "//span[text()='Next']").click()
                time.sleep(3)
                
                # Check for verification code input
                code_input = driver.find_element(By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")
                if code_input:
                    verification_code = get_verification_code_from_gmail(your_email, gmail_password)
                    if verification_code:
                        print(f"Email verification code found: {verification_code}")
                        send_telegram_message(f"📧 Email verification code found: {verification_code}")
                        code_input.send_keys(verification_code)
                        driver.find_element(By.XPATH, "//span[text()='Next']").click()
                        time.sleep(3)
        except:
            pass

        # Step 3: Handle username verification if needed
        try:
            verify_username = driver.find_element(
                By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"
            )
            if verify_username:
                print("Username verification required")
                send_telegram_message("👤 Username verification required")
                verify_username.send_keys("kkittyy864")
                driver.find_element(By.XPATH, "//span[text()='Next']").click()
                time.sleep(3)
        except:
            pass

        # Step 4: Enter password
        password_field = driver.find_element(
            By.XPATH, "//input[@autocomplete='current-password']"
        )
        password_field.send_keys(your_password)
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        time.sleep(5)

        # Step 5: Handle post-login verification code if needed
        try:
            verification_input = driver.find_element(By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']")
            if verification_input:
                print("Post-login verification code required")
                send_telegram_message("🔐 Post-login verification code required")
                
                max_attempts = 5
                verification_code = None
                
                for attempt in range(max_attempts):
                    verification_code = get_verification_code_from_gmail(your_email, gmail_password)
                    if verification_code:
                        break
                    print(f"Attempt {attempt + 1}: Waiting for verification code...")
                    send_telegram_message(f"⏳ Attempt {attempt + 1}: Waiting for verification code...")
                    time.sleep(10)
                
                if verification_code:
                    print(f"Post-login verification code found: {verification_code}")
                    send_telegram_message(f"🔑 Post-login verification code found: {verification_code}")
                    verification_input.send_keys(verification_code)
                    driver.find_element(By.XPATH, "//span[text()='Next']").click()
                    time.sleep(5)
                else:
                    print("Failed to get verification code")
                    send_telegram_message("❌ Failed to get verification code")
                    return False
        except Exception as e:
            print(f"No post-login verification needed or error: {str(e)}")
            pass

        return True
    except Exception as e:
        print(f"Login failed: {str(e)}")
        send_telegram_message(f"❌ Login failed: {str(e)}")
        return False


def read_existing_usernames(target_username):
    filename = f"{target_username}_following.txt"
    try:
        with open(filename, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


def write_new_usernames(target_username, usernames):
    filename = f"{target_username}_following.txt"
    with open(filename, "a") as f:
        for username in usernames:
            f.write(f"{username}\n")


def get_following_list(target_username, your_email, your_password, gmail_password):
    driver = None
    try:
        existing_usernames = read_existing_usernames(target_username)
        print(f"Found {len(existing_usernames)} existing usernames in {target_username}_following.txt")

        # Send initial status to Telegram
        send_telegram_message(
            f"🤖 Starting to check @{target_username}'s following list\nExisting usernames: {len(existing_usernames)}"
        )

        # Modified Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Using new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")  # Set specific window size
        chrome_options.add_argument("--force-device-scale-factor=1")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set window size programmatically as well
        driver.set_window_size(1920, 1080)

        if not login_to_twitter(driver, your_email, your_password, gmail_password):
            send_telegram_message("❌ Failed to login to Twitter")
            return

        driver.get(f"https://twitter.com/{target_username}/following")
        time.sleep(5)

        if not verify_page_loaded(driver):
            send_telegram_message("❌ Failed to load following page correctly")
            return

        following_accounts = set()
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 5

        while scroll_attempts < max_attempts:
            wait = WebDriverWait(driver, 10)
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        '[data-testid="primaryColumn"] section[role="region"]',
                    )
                )
            )

            user_cells = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-testid="primaryColumn"] section[role="region"] [data-testid="UserCell"]',
            )
            print(f"Found {len(user_cells)} users in this scroll")

            for user in user_cells:
                try:
                    username_elements = user.find_elements(
                        By.CSS_SELECTOR,
                        'div.css-175oi2r > a > div.css-175oi2r > div[dir="ltr"] > span.css-1jxf684',
                    )
                    for element in username_elements:
                        username_text = element.text
                        if username_text and "@" in username_text:
                            following_accounts.add(username_text)
                            break
                except Exception as e:
                    continue

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_height = new_height

        new_usernames = following_accounts - existing_usernames

        print(f"Following accounts: {following_accounts}")
        print(f"Existing usernames: {existing_usernames}")
        print(f"New usernames: {new_usernames}")

        # Send summary to Telegram
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_message = f"""
📊 Following Check Summary for @{target_username}
🕒 Time: {timestamp}
👥 Total accounts found: {len(following_accounts)}
"""
        send_telegram_message(summary_message)

        # If there are new usernames, send them to Telegram
        if new_usernames:
            new_usernames_message = f"""
🆕 New Accounts Found ({len(new_usernames)}):
"""
            for i, account in enumerate(sorted(new_usernames), 1):
                new_usernames_message += f"{i}. {account}\n"

            # Split message if it's too long
            if len(new_usernames_message) > 4000:
                chunks = [
                    new_usernames_message[i : i + 4000]
                    for i in range(0, len(new_usernames_message), 4000)
                ]
                for chunk in chunks:
                    send_telegram_message(chunk)
            else:
                send_telegram_message(new_usernames_message)

            # Update the file with new usernames using target username
            write_new_usernames(target_username, new_usernames)
            send_telegram_message(f"✅ New usernames have been added to {target_username}_following.txt")
        else:
            send_telegram_message("ℹ️ No new accounts found")

    except Exception as e:
        error_message = f"❌ An error occurred: {str(e)}"
        send_telegram_message(error_message)
    finally:
        if driver:
            driver.quit()


def verify_page_loaded(driver):
    try:
        wait = WebDriverWait(driver, 10)
        following_text = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="primaryColumn"] [role="heading"]')
            )
        )
        print(f"Page heading found: {following_text.text}")

        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    '[data-testid="primaryColumn"] section[role="region"]',
                )
            )
        )

        user_cells = driver.find_elements(
            By.CSS_SELECTOR,
            '[data-testid="primaryColumn"] section[role="region"] [data-testid="UserCell"]',
        )
        print(f"Found {len(user_cells)} users in Following section in this scroll")

        return True
    except Exception as e:
        print(f"Error verifying page load: {str(e)}")
        return False


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def stable_find_element(driver, by, value):
    return driver.find_element(by, value)


if __name__ == "__main__":
    target_username = "miiirshah"
    your_email = "kkittyy864@gmail.com"
    your_password = "Salam123456789?"
    gmail_password = "cnfu mejh jxbv zopu"  # Add your Gmail app password here

    get_following_list(target_username, your_email, your_password, gmail_password)
