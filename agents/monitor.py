import os
import glob
import json
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from typing import List, Dict
from pathlib import Path

try:
    import feedparser
except ImportError:
    feedparser = None

# Data sources
RBI_FEEDS = {
    "notifications": "https://www.rbi.org.in/english/RSS.aspx?ID=165",
    "pressreleases": "https://www.rbi.org.in/english/RSS.aspx?ID=35",
}

SEBI_URLS = {
    "circulars": "https://www.sebi.gov.in/sebiweb/other/OtherMainAction.do?doRecognised=yes&intmnuid=13",
}

MCA_URLS = {
    "notifications": "https://www.mca.gov.in/content/dam/mca/notification/",
}

IRDAI_URLS = {
    "circulars": "https://irdai.gov.in/document-library",
}

# Track last checked time
LAST_CHECKED_FILE = "data/last_checked.json"

def _load_last_checked():
    """Load the last check timestamp."""
    if os.path.exists(LAST_CHECKED_FILE):
        with open(LAST_CHECKED_FILE, 'r') as f:
            data = json.load(f)
            return data.get("last_checked", None)
    return None

def _save_last_checked():
    """Save current timestamp as last check time."""
    os.makedirs(os.path.dirname(LAST_CHECKED_FILE), exist_ok=True)
    with open(LAST_CHECKED_FILE, 'w') as f:
        json.dump({"last_checked": datetime.now().isoformat()}, f)

def _fetch_rbi_circulars() -> List[Dict]:
    """Fetch latest RBI circulars from RSS feeds."""
    if not feedparser:
        print("Warning: feedparser not installed. Skipping RBI feed.")
        return []
    
    circulars = []
    for feed_type, feed_url in RBI_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Get last 5 entries
                circular = {
                    "source": "RBI",
                    "type": feed_type,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:500],
                }
                circulars.append(circular)
        except Exception as e:
            print(f"Error fetching RBI {feed_type}: {e}")
    
    return circulars

def _fetch_sebi_circulars() -> List[Dict]:
    """Fetch SEBI circulars via web scraping."""
    circulars = []
    try:
        from bs4 import BeautifulSoup
        
        for feed_type, url in SEBI_URLS.items():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find PDF links (SEBI typically lists PDFs)
            for link in soup.find_all('a', href=True)[:5]:
                href = link['href']
                if '.pdf' in href.lower():
                    circular = {
                        "source": "SEBI",
                        "type": feed_type,
                        "title": link.get_text(strip=True),
                        "link": href if href.startswith('http') else f"https://www.sebi.gov.in{href}",
                        "published": datetime.now().isoformat(),
                    }
                    circulars.append(circular)
    except Exception as e:
        print(f"Error fetching SEBI circulars: {e}")
    
    return circulars

def _fetch_mca_notices() -> List[Dict]:
    """Fetch MCA notices via web scraping."""
    notices = []
    try:
        from bs4 import BeautifulSoup
        
        for notice_type, url in MCA_URLS.items():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find PDF links
            for link in soup.find_all('a', href=True)[:5]:
                href = link['href']
                if '.pdf' in href.lower():
                    notice = {
                        "source": "MCA",
                        "type": notice_type,
                        "title": link.get_text(strip=True),
                        "link": href if href.startswith('http') else f"https://www.mca.gov.in{href}",
                        "published": datetime.now().isoformat(),
                    }
                    notices.append(notice)
    except Exception as e:
        print(f"Error fetching MCA notices: {e}")
    
    return notices

def _fetch_irdai_circulars() -> List[Dict]:
    """Fetch IRDAI circulars via web scraping."""
    circulars = []
    try:
        from bs4 import BeautifulSoup
        
        for doc_type, url in IRDAI_URLS.items():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True)[:5]:
                href = link['href']
                if '.pdf' in href.lower():
                    circular = {
                        "source": "IRDAI",
                        "type": doc_type,
                        "title": link.get_text(strip=True) or "IRDAI Document",
                        "link": href if href.startswith('http') else f"https://irdai.gov.in{href}",
                        "published": datetime.now().isoformat(),
                    }
                    circulars.append(circular)
    except Exception as e:
        print(f"Error fetching IRDAI circulars: {e}")
    
    return circulars

def _download_pdf(url: str, filename: str) -> bool:
    """Download PDF from URL and save locally."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        os.makedirs("data/incoming", exist_ok=True)
        filepath = os.path.join("data/incoming", filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

@tool
def check_new_circulars(mode: str = "demo") -> list:
    """
    Check for new regulatory circulars from RBI, SEBI, and MCA.
    
    Args:
        mode: "demo" (local folder) or "live" (fetch from regulatory sources)
    
    Returns:
        List of PDF file paths
    """
    if mode == "demo":
        # Check local incoming folder
        incoming_dir = os.path.join("data", "incoming")
        if not os.path.exists(incoming_dir):
            os.makedirs(incoming_dir, exist_ok=True)
        
        pdfs = glob.glob(os.path.join(incoming_dir, "*.pdf"))
        return pdfs
    
    elif mode == "live":
        print("🔄 Fetching live circulars from RBI, SEBI, and MCA...")
        
        all_sources = []
        all_sources.extend(_fetch_rbi_circulars())
        all_sources.extend(_fetch_sebi_circulars())
        all_sources.extend(_fetch_mca_notices())
        all_sources.extend(_fetch_irdai_circulars())
        
        print(f"Found {len(all_sources)} new circulars")
        
        # Download PDFs
        downloaded_files = []
        for i, source in enumerate(all_sources):
            filename = f"{source['source']}_{source['type']}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            if _download_pdf(source['link'], filename):
                downloaded_files.append(os.path.join("data/incoming", filename))
        
        _save_last_checked()
        
        print(f"✅ Downloaded {len(downloaded_files)} PDFs")
        return downloaded_files
    
    return []
