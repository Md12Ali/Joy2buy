#!/usr/bin/env python3
"""
JOY2BUY Website Validator & Screenshot Capture
Validates HTML, CSS, and JavaScript, then captures screenshots
Run this script on your local computer (not in cloud)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Configuration
WEBSITE_URL = "https://joy2buy-shop-218caf987cba.herokuapp.com/"
OUTPUT_DIR = "./assets/images/validation"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def initialize_driver():
    """Initialize Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment to run headless
    options.add_argument("--window-size=1440,900")
    driver = webdriver.Chrome(options=options)
    return driver

def capture_website(driver):
    """Capture screenshot of the live website"""
    print("\n📸 STEP 1: Capturing website homepage...")
    driver.get(WEBSITE_URL)
    time.sleep(3)
    driver.save_screenshot(f"{OUTPUT_DIR}/website-homepage.png")
    print(f"✅ Saved: website-homepage.png")

def validate_html(driver):
    """Validate HTML with W3C Validator and capture screenshot"""
    print("\n🔍 STEP 2: Validating HTML with W3C Validator...")
    driver.get("https://validator.w3.org/")
    time.sleep(2)

    # Find URL input field and enter website URL
    url_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "uri"))
    )
    url_input.clear()
    url_input.send_keys(WEBSITE_URL)
    time.sleep(1)

    # Click Check button
    check_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    check_button.click()

    # Wait for validation results
    time.sleep(6)
    driver.save_screenshot(f"{OUTPUT_DIR}/html-validation.png")
    print(f"✅ Saved: html-validation.png")

def validate_css(driver):
    """Validate CSS with Jigsaw W3C Validator and capture screenshot"""
    print("\n🎨 STEP 3: Validating CSS with Jigsaw Validator...")
    driver.get("https://jigsaw.w3.org/css-validator/")
    time.sleep(2)

    # Find URL input field
    url_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "uri"))
    )
    url_input.clear()
    url_input.send_keys(WEBSITE_URL)
    time.sleep(1)

    # Click Check button
    check_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    check_button.click()

    # Wait for validation results
    time.sleep(6)
    driver.save_screenshot(f"{OUTPUT_DIR}/css-validation.png")
    print(f"✅ Saved: css-validation.png")

def check_javascript(driver):
    """Check JavaScript console and capture screenshot"""
    print("\n💻 STEP 4: Checking JavaScript console for errors...")
    driver.get(WEBSITE_URL)
    time.sleep(3)

    # Get console logs
    logs = driver.get_log('browser')

    # Print console info
    print(f"\n📋 Console Logs ({len(logs)} entries):")
    errors = [log for log in logs if log['level'] == 'SEVERE']
    if errors:
        print(f"⚠️  ERRORS FOUND: {len(errors)}")
        for error in errors:
            print(f"   - {error['message']}")
    else:
        print("✅ No JavaScript errors found!")

    # Capture screenshot
    driver.save_screenshot(f"{OUTPUT_DIR}/javascript-validation.png")
    print(f"✅ Saved: javascript-validation.png")

def main():
    """Main function"""
    print("="*70)
    print("🚀 JOY2BUY WEBSITE VALIDATOR & SCREENSHOT CAPTURE")
    print("="*70)

    driver = None
    try:
        driver = initialize_driver()

        # Run validations
        capture_website(driver)
        validate_html(driver)
        validate_css(driver)
        check_javascript(driver)

        print("\n" + "="*70)
        print("✅ ALL VALIDATIONS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📁 Screenshots saved to: {OUTPUT_DIR}/")
        print("   - website-homepage.png")
        print("   - html-validation.png")
        print("   - css-validation.png")
        print("   - javascript-validation.png")
        print("\n📝 Next steps:")
        print("   1. Review the screenshots in the validation folder")
        print("   2. Commit and push to GitHub")
        print("   3. README will be updated with validation links")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure:")
        print("   - Chrome is installed")
        print("   - ChromeDriver is in PATH or in the same directory")
        print("   - You have internet connection")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
