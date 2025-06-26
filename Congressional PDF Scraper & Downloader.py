import os
import sys

# When bundled by PyInstaller, browsers live in _MEIPASS/ms-playwright
if getattr(sys, "frozen", False):
    bundle_root = sys._MEIPASS
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(bundle_root, "ms-playwright")

import re
import requests
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import subprocess

# Ensure Playwright browsers are installed
try:
    subprocess.run(["playwright", "install", "chromium"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    print("⚠️ Failed to auto-install Playwright browsers. Please run 'playwright install'.")


def get_user_inputs():
    known_years = list(range(2024, 2007, -1))
    while True:
        try:
            print("Available years: 2024–2008")
            year = int(input("\n💓️ Enter the year you'd like to download PDFs for (e.g., 2022):\n→ "))
            if year not in known_years:
                print("⚠️ That year may not be available. Please try one of the listed years.")
                continue
            break
        except ValueError:
            print("❌ Invalid year. Please enter a valid 4-digit year like 2022.")
    last_name = input("\n👤 Enter a last name to search (e.g., Smith):\n→ ").strip()
    return str(year), last_name


def download_disclosure_pdfs(year, last_name):
    print(f"\n🌐 Downloading PDF reports for {year} (Last Name: {last_name})...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://disclosures-clerk.house.gov/FinancialDisclosure#Search")

        # fill in the search form
        page.wait_for_selector("#search-members", timeout=10000)
        page.click("#search-members")
        page.wait_for_selector("input[name='LastName']", timeout=10000)
        page.fill("input[name='LastName']", last_name)
        page.select_option("select[name='FilingYear']", label=year)
        page.click("button:has-text('Search')")

        # collect PDF links
        page.wait_for_selector("#DataTables_Table_0 a[href$='.pdf']", timeout=20000)
        links = page.query_selector_all("#DataTables_Table_0 a[href$='.pdf']")

        # create output folder
        folder = f"pdfs_{year}"
        os.makedirs(folder, exist_ok=True)

        for i, link in enumerate(links):
            href = link.get_attribute("href")
            raw = link.inner_text().strip()
            safe = re.sub(r'[\\/*?:"<>|]', '_', raw) or f"report_{i}"
            path = os.path.join(folder, f"{safe}_{i}.pdf")

            # download and save
            resp = requests.get(urljoin("https://disclosures-clerk.house.gov/", href))
            with open(path, 'wb') as f:
                f.write(resp.content)
            print(f"✅ Downloaded: {path}")

        browser.close()


def main():
    while True:
        year, last_name = get_user_inputs()
        download_disclosure_pdfs(year, last_name)

        again = input("\n🔄 Download another last name? (y/n):\n→ ").strip().lower()
        if again not in ('y', 'yes'):
            print("👋 All done!")
            break


if __name__ == '__main__':
    main()
