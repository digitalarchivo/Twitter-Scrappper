from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from datetime import datetime

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


def login_to_twitter(driver, your_email, your_password):
    try:
        driver.get("https://twitter.com/i/flow/login")
        time.sleep(3)

        email_field = driver.find_element(By.XPATH, "//input[@autocomplete='username']")
        email_field.send_keys(your_email)
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        time.sleep(3)

        try:
            verify_email = driver.find_element(
                By.XPATH, "//input[@autocomplete='email']"
            )
            if verify_email:
                verify_email.send_keys("kkittyy864@gmail.com")
                driver.find_element(By.XPATH, "//span[text()='Next']").click()
                time.sleep(3)
        except:
            pass

        try:
            verify_username = driver.find_element(
                By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']"
            )
            if verify_username:
                verify_username.send_keys("kkittyy864")
                driver.find_element(By.XPATH, "//span[text()='Next']").click()
                time.sleep(3)
        except:
            pass

        password_field = driver.find_element(
            By.XPATH, "//input[@autocomplete='current-password']"
        )
        password_field.send_keys(your_password)
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        time.sleep(5)

        return True
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False


def read_existing_usernames(filename):
    try:
        with open(filename, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


def write_new_usernames(filename, usernames):
    with open(filename, "a") as f:
        for username in usernames:
            f.write(f"{username}\n")


def get_following_list(target_username, your_email, your_password):
    driver = None
    try:
        filename = "usernames.txt"
        existing_usernames = read_existing_usernames(filename)
        print(f"Found {len(existing_usernames)} existing usernames in file")

        # Send initial status to Telegram
        send_telegram_message(
            f"🤖 Starting to check @{target_username}'s following list\nExisting usernames: {len(existing_usernames)}"
        )

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        if not login_to_twitter(driver, your_email, your_password):
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

            # Update the file with new usernames
            write_new_usernames(filename, new_usernames)
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


if __name__ == "__main__":
    target_username = "arashselective"
    your_email = "kkittyy864@gmail.com"
    your_password = "Salam123456789?"

    get_following_list(target_username, your_email, your_password)
