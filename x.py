import sys
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# -------- Config --------
if len(sys.argv) != 2:
    print("Usage: python x.py <twitter_username>")
    sys.exit(1)

username = sys.argv[1]  # e.g., shawmakesmagic
url = f"https://twitter.com/{username}/following"
output_file = f"{username}_following.txt"
# ------------------------

# Setup Chrome driver with headless options
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

chromedriver_path = shutil.which("chromedriver")
if chromedriver_path is None:
    raise RuntimeError("chromedriver binary not found in PATH")

driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
driver.get(url)
time.sleep(5)

# Scroll to load more following entries
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

elements = driver.find_elements(By.XPATH, '//div[@data-testid="UserCell"]//a[contains(@href,"/")]')

seen = set()
usernames = []
for el in elements:
    href = el.getAttribute("href")
    if href and f"/{username}" not in href:
        handle = href.strip("/").split("/")[-1]
        if handle not in seen:
            usernames.append(handle)
            seen.add(handle)

# Save to dynamic file
with open(output_file, "w", encoding="utf-8") as f:
    for handle in usernames:
        f.write(f"{handle}\n")

print(f"Saved {len(usernames)} usernames to {output_file}")
driver.quit()
