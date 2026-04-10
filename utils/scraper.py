import os
import json
import requests
import shutil
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

LAST_CHECKED_FILE = Path("data/last_checked.json")

def _load_last_checked() -> dict:
    if LAST_CHECKED_FILE.exists():
        with open(LAST_CHECKED_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_last_checked(url: str):
    LAST_CHECKED_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = _load_last_checked()
    data[url] = datetime.now().isoformat()
    with open(LAST_CHECKED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_latest_circular_mock() -> str:
    """
    Uses BeautifulSoup to parse regulatory HTML and find a PDF link.
    Date-aware: tracks when each source was last checked using last_checked.json.
    Returns the absolute path to the saved circular PDF.
    """
    # Simulated HTML representing an RBI-style circulars page
    dummy_html = """
    <html>
        <body>
            <h1>RBI Latest Circulars</h1>
            <div class="circular-list">
                <a class="pdf-link" href="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf">
                    Master Direction - KYC Updated April 2024
                </a>
            </div>
        </body>
    </html>
    """

    soup = BeautifulSoup(dummy_html, "html.parser")
    link_tag = soup.find('a', class_='pdf-link')
    scraped_url = link_tag['href']
    print(f"Scraper found link via BeautifulSoup: {scraped_url}")

    # Date-aware check: log this URL with a timestamp
    last_checked = _load_last_checked()
    if scraped_url in last_checked:
        print(f"Source last checked: {last_checked[scraped_url]}")
    else:
        print(f"New source detected — first time scraping this URL.")
    _save_last_checked(scraped_url)

    # Save destination
    incoming_dir = Path("data/incoming")
    incoming_dir.mkdir(parents=True, exist_ok=True)
    live_target = incoming_dir / "live_scraped_circular.pdf"

    # Use demo_new.pdf as the mocked downloaded circular (valid PDF for PyMuPDF)
    demo_new_path = Path("data/circulars/new/demo_new.pdf")
    if demo_new_path.exists():
        shutil.copy(demo_new_path, live_target)
        print(f"Saved circular to: {live_target.absolute()}")
        return str(live_target.absolute())
    else:
        raise FileNotFoundError("Demo PDF not found at data/circulars/new/demo_new.pdf")
