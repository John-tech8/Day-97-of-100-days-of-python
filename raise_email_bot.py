"""
raise_email_bot.py
==================
Automates sending a professional raise-request email to your boss
every 3 months via Gmail, using Selenium.

Requirements:
    pip install selenium schedule

Setup:
    1. Download ChromeDriver matching your Chrome version:
       https://chromedriver.chromium.org/downloads
    2. Fill in the CONFIG block below.
    3. Enable "Less Secure App Access" in your Gmail account,
       OR use an App Password (recommended):
       https://support.google.com/accounts/answer/185833

Run:
    python raise_email_bot.py
"""

import random
import time
import logging
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────────────────────────────────────────
#  CONFIG  ← edit this section
# ─────────────────────────────────────────────
CONFIG = {
    "your_email":      "you@gmail.com",          # Your Gmail address
    "your_password":   "your_app_password_here", # Gmail App Password (recommended)
    "boss_email":      "boss@company.com",        # Your boss's email
    "your_name":       "Your Name",
    "boss_name":       "Boss Name",
    "your_role":       "Software Engineer",
    "chromedriver_path": "/usr/local/bin/chromedriver",  # Path to chromedriver
    "headless":        False,  # Set True to run silently in background
}
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler("raise_bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Email Templates ──────────────────────────────────────────────────────────

SUBJECTS = [
    "Compensation Review Request",
    "Request for Salary Discussion",
    "Checking In: Compensation Alignment",
    "Would Love to Discuss My Compensation",
    "Salary Review – {name}",
]

BODIES = [
    """\
Hi {boss},

I hope you're doing well! I wanted to reach out to discuss the possibility \
of a salary review.

Over the past few months, I've taken on additional responsibilities as a \
{role} and have consistently delivered results. I believe my compensation \
should reflect the value and growth I've brought to the team.

I'd love to schedule a brief meeting at your convenience to discuss this further. \
Please let me know a time that works best for you.

Thank you for your time and consideration.

Best regards,
{name}
""",
    """\
Hi {boss},

I hope this message finds you well. I'm writing to formally request a \
compensation review.

Since my last review, I have taken on expanded responsibilities, contributed \
to key projects, and continued to grow in my role as {role}. I feel it would \
be a great time to revisit my current salary to ensure it remains competitive \
and aligned with my contributions.

I would appreciate the opportunity to discuss this with you. Would you be open \
to a quick 15-minute call this week or next?

Thank you so much for your consideration — I truly enjoy working here and look \
forward to continuing to contribute to the team's success.

Warm regards,
{name}
""",
    """\
Hello {boss},

I wanted to take a moment to discuss something that's been on my mind. \
As we approach the end of this quarter, I'd like to request a formal review \
of my compensation as {role}.

I've been focused on delivering high-quality work and contributing positively \
to our team's goals, and I believe this is a good time to ensure my \
compensation reflects that commitment and growth.

I'd welcome any chance to discuss this in more detail — even a short \
conversation would be greatly appreciated.

Thanks in advance,
{name}
""",
]


def build_email():
    """Randomly pick a subject and body template and fill in placeholders."""
    subject = random.choice(SUBJECTS).format(name=CONFIG["your_name"])
    body = random.choice(BODIES).format(
        boss=CONFIG["boss_name"],
        name=CONFIG["your_name"],
        role=CONFIG["your_role"],
    )
    return subject, body


# ── Selenium / Gmail logic ───────────────────────────────────────────────────

def get_driver():
    opts = Options()
    if CONFIG["headless"]:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(CONFIG["chromedriver_path"])
    return webdriver.Chrome(service=service, options=opts)


def login_gmail(driver, wait):
    log.info("Navigating to Gmail …")
    driver.get("https://mail.google.com")

    # Enter email
    wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
    driver.find_element(By.ID, "identifierId").send_keys(CONFIG["your_email"])
    driver.find_element(By.ID, "identifierNext").click()
    time.sleep(2)

    # Enter password
    wait.until(EC.element_to_be_clickable((By.NAME, "Passwd")))
    driver.find_element(By.NAME, "Passwd").send_keys(CONFIG["your_password"])
    driver.find_element(By.ID, "passwordNext").click()

    # Wait for inbox to load
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='main']")))
    log.info("Logged in successfully.")


def compose_and_send(driver, wait, subject, body):
    log.info("Opening compose window …")

    # Click "Compose"
    compose_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'T-I-KE')]"))
    )
    compose_btn.click()
    time.sleep(1.5)

    # To field
    to_field = wait.until(
        EC.presence_of_element_located((By.XPATH, "//textarea[@name='to']"))
    )
    to_field.send_keys(CONFIG["boss_email"])
    to_field.send_keys(Keys.TAB)
    time.sleep(0.5)

    # Subject field
    subj_field = driver.find_element(By.NAME, "subjectbox")
    subj_field.send_keys(subject)
    time.sleep(0.5)

    # Body field
    body_field = driver.find_element(
        By.XPATH, "//div[@aria-label='Message Body']"
    )
    body_field.click()
    body_field.send_keys(body)
    time.sleep(0.5)

    # Send
    send_btn = driver.find_element(
        By.XPATH, "//div[@aria-label='Send ‪(Ctrl-Enter)‬']"
    )
    send_btn.click()
    log.info("✅  Email sent successfully!")


def send_raise_email():
    log.info("=" * 55)
    log.info("Starting raise-email job  %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    driver = get_driver()
    wait = WebDriverWait(driver, 20)
    try:
        login_gmail(driver, wait)
        subject, body = build_email()
        log.info("Subject: %s", subject)
        compose_and_send(driver, wait, subject, body)
    except Exception as exc:
        log.error("Something went wrong: %s", exc, exc_info=True)
    finally:
        time.sleep(3)
        driver.quit()
        log.info("Browser closed.")


# ── Scheduler ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Raise Email Bot started 🚀")
    log.info("Will send an email every 3 months.")
    log.info("Next run scheduled in approx. 90 days.")

    # Send one immediately so you can verify it works
    send_raise_email()

    # Then schedule every 90 days
    schedule.every(90).days.do(send_raise_email)

    while True:
        schedule.run_pending()
        time.sleep(3600)   # check every hour
