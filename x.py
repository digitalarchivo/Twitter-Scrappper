import sys
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if len(sys.argv) != 2:
    print("Usage: python x.py <twitter_username>")
    sys.exit(1)

username = sys.argv[1]
url = f"https://twitter.com/{username}/following"
output_file = f"{username}_following.txt"

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-dev-shm-usage")  # For some Linux containers

chromedriver_path = shutil.which("chromedriver")
if chromedriver_path is None:
    raise RuntimeError("chromedriver binary not found in PATH")

driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
driver.get(url)

wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="UserCell"]')))

# Scroll repeatedly to load more followings
last_height = driver.execute_script("return document.body.scrollHeight")
for _ in range(10):  # scroll more times for better loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Extract usernames from UserCell links
elements = driver.find_elements(By.XPATH, '//div[@data-testid="UserCell"]//a[contains(@href,"/")]')

seen = set()
usernames = []
for el in elements:
    href = el.get_attribute("href")
    if href and href.startswith("https://twitter.com/"):
        handle = href.split("https://twitter.com/")[-1].strip("/")
        # Exclude the original username or empty strings
        if handle and handle.lower() != username.lower() and handle not in seen:
            usernames.append(handle)
            seen.add(handle)

with open(output_file, "w", encoding="utf-8") as f:
    for handle in usernames:
        f.write(f"{handle}\n")

print(f"Saved {len(usernames)} usernames to {output_file}")
driver.quit()
