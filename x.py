import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load usernames from environment
usernames = os.getenv("TARGET_USERNAMES")
if not usernames:
    print("❌ No usernames provided. Please set the TARGET_USERNAMES environment variable.")
    exit(1)

usernames = [u.strip().lstrip('@') for u in usernames.split(',') if u.strip()]

# Twitter login credentials (set these securely in GitHub Secrets)
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")

if not TWITTER_EMAIL or not TWITTER_PASSWORD:
    print("❌ Twitter login credentials not found. Please set TWITTER_EMAIL and TWITTER_PASSWORD.")
    exit(1)

# Setup headless Chrome
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

def login_to_twitter():
    print("🔐 Logging into Twitter...")
    driver.get("https://twitter.com/login")

    wait.until(EC.presence_of_element_located((By.NAME, "text"))).send_keys(TWITTER_EMAIL)
    driver.find_element(By.XPATH, "//span[text()='Next']").click()
    time.sleep(2)

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(TWITTER_PASSWORD)
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        print("✅ Logged in successfully.")
    except Exception as e:
        print("❌ Login failed.")
        driver.quit()
        exit(1)

    time.sleep(5)

def scrape_following(username):
    print(f"🔍 Processing @{username}")
    driver.get(f"https://twitter.com/{username}/following")
    time.sleep(3)

    last_height = driver.execute_script("return document.body.scrollHeight")
    SCROLL_PAUSE = 2
    scroll_attempts = 0

    # Scroll to load all followings
    while scroll_attempts < 10:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
        last_height = new_height

    # Parse usernames
    elements = driver.find_elements(By.XPATH, '//div[@data-testid="UserCell"]//div[@dir="ltr"]/span')
    following_usernames = [el.text for el in elements if el.text.startswith('@')]

    output_filename = f"{username}_following.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for user in following_usernames:
            f.write(f"{user}\n")

    print(f"✅ @{username} is following {len(following_usernames)} users. Saved to {output_filename}.")

# --- Execution ---
login_to_twitter()

for username in usernames:
    scrape_following(username)

driver.quit()
print("🏁 Done.")
