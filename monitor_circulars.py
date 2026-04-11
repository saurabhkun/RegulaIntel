"""
Live Circular Monitoring & Processing Pipeline
Continuously monitors RBI, SEBI, and MCA for new regulatory circulars.
"""

import os
import time
import json
import glob
import requests
from datetime import datetime
from pathlib import Path
from agents.workflow import graph as workflow_graph
from dotenv import load_dotenv

try:
    import feedparser
except ImportError:
    feedparser = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

load_dotenv(override=True)

MONITORING_CONFIG = {
    "check_interval": 3600,  # Check every hour (3600 seconds)
    "auto_process": True,    # Automatically process new circulars
    "archive_old_pdfs": True,
    "log_file": "data/monitoring.log"
}

def log_message(message: str):
    """Log monitoring activity with proper UTF-8 encoding for emoji support."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    os.makedirs(os.path.dirname(MONITORING_CONFIG["log_file"]), exist_ok=True)
    
    # For log file, use UTF-8 encoding to support emojis
    with open(MONITORING_CONFIG["log_file"], 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")

def archive_old_pdfs(days: int = 7):
    """Archive PDFs older than specified days."""
    import shutil
    
    incoming_dir = Path("data/incoming")
    archive_dir = Path("data/circulars/old")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    if not incoming_dir.exists():
        return
    
    cutoff_time = time.time() - (days * 86400)
    
    for pdf in incoming_dir.glob("*.pdf"):
        if pdf.stat().st_mtime < cutoff_time:
            try:
                shutil.move(str(pdf), str(archive_dir / pdf.name))
                log_message(f"Archived old PDF: {pdf.name}")
            except Exception as e:
                log_message(f"Error archiving {pdf.name}: {e}")

def _fetch_rbi_circulars():
    """Fetch latest RBI circulars from RSS feeds."""
    if not feedparser:
        return []
    
    RBI_FEEDS = {
        "notifications": "https://www.rbi.org.in/english/RSS.aspx?ID=165",
        "pressreleases": "https://www.rbi.org.in/english/RSS.aspx?ID=35",
    }
    
    circulars = []
    for feed_type, feed_url in RBI_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                circular = {
                    "source": "RBI",
                    "type": feed_type,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                }
                circulars.append(circular)
        except Exception as e:
            log_message(f"Error fetching RBI {feed_type}: {e}")
    
    return circulars

def _fetch_sebi_circulars():
    """Fetch SEBI circulars via web scraping."""
    if not BeautifulSoup:
        return []
    
    SEBI_URLS = {
        "circulars": "https://www.sebi.gov.in/sebiweb/other/OtherMainAction.do?doRecognised=yes&intmnuid=13",
    }
    
    circulars = []
    for feed_type, url in SEBI_URLS.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            log_message(f"Error fetching SEBI circulars: {e}")
    
    return circulars

def _fetch_mca_notices():
    """Fetch MCA notices via web scraping."""
    if not BeautifulSoup:
        return []
    
    MCA_URLS = {
        "notifications": "https://www.mca.gov.in/content/dam/mca/notification/",
    }
    
    notices = []
    for notice_type, url in MCA_URLS.items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            log_message(f"Error fetching MCA notices: {e}")
    
    return notices

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def _download_pdf(url: str, filename: str) -> bool:
    """Download PDF from URL and save locally."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        os.makedirs("data/incoming", exist_ok=True)
        filepath = os.path.join("data/incoming", filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        log_message(f"Downloaded: {filepath}")
        return True
    except Exception as e:
        log_message(f"Error downloading {url}: {e}")
        return False

def _check_new_circulars_local(mode: str = "demo"):
    """Check for new regulatory circulars from RBI, SEBI, and MCA."""
    if mode == "demo":
        incoming_dir = os.path.join("data", "incoming")
        if not os.path.exists(incoming_dir):
            os.makedirs(incoming_dir, exist_ok=True)
        
        pdfs = glob.glob(os.path.join(incoming_dir, "*.pdf"))
        return pdfs
    
    elif mode == "live":
        log_message("Fetching live circulars from RBI, SEBI, and MCA...")
        
        all_sources = []
        all_sources.extend(_fetch_rbi_circulars())
        all_sources.extend(_fetch_sebi_circulars())
        all_sources.extend(_fetch_mca_notices())
        
        log_message(f"Found {len(all_sources)} circulars to process")
        
        # Download PDFs
        downloaded_files = []
        for i, source in enumerate(all_sources):
            filename = f"{source['source']}_{source['type']}_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            if _download_pdf(source['link'], filename):
                downloaded_files.append(os.path.join("data/incoming", filename))
        
        # Save last checked time
        os.makedirs("data", exist_ok=True)
        with open("data/last_checked.json", 'w', encoding='utf-8') as f:
            json.dump({"last_checked": datetime.now().isoformat()}, f)
        
        log_message(f"Downloaded {len(downloaded_files)} PDFs")
        return downloaded_files
    
    return []


def process_new_circular(pdf_path: str, old_baseline: str = None):
    """Process a new circular through the compliance workflow."""
    try:
        log_message(f"Processing: {pdf_path}")
        
        # Use most recent baseline or hardcoded baseline
        if not old_baseline:
            baseline_dir = "data/circulars/old"
            pdfs = list(sorted(Path(baseline_dir).glob("*.pdf"), reverse=True))
            old_baseline = str(pdfs[0]) if pdfs else "data/baseline.pdf"
        
        # Run workflow
        result = workflow_graph.invoke({
            "old_pdf": old_baseline,
            "new_pdf": pdf_path,
            "changes": [],
            "impacts": [],
            "amendments": [],
            "next": ""
        })
        
        # Generate report
        amendments_count = len(result.get("amendments", []))
        impacts_count = len(result.get("impacts", []))
        
        log_message(f"✅ Processed {os.path.basename(pdf_path)} | "
                   f"Impacts: {impacts_count} | Amendments: {amendments_count}")
        
        return result
        
    except Exception as e:
        log_message(f"❌ Error processing {pdf_path}: {str(e)}")
        return None

def run_live_monitor(interval: int = None, continuous: bool = False):
    """
    Run the live monitoring system.
    
    Args:
        interval: Check interval in seconds (default: 3600)
        continuous: Keep running indefinitely
    """
    interval = interval or MONITORING_CONFIG["check_interval"]
    
    log_message("🚀 Starting Live Regulatory Monitoring")
    log_message("Monitoring: RBI, SEBI, MCA")
    log_message(f"Check interval: {interval}s")
    
    try:
        while True:
            log_message("🔄 Checking for new circulars...")
            
            # Fetch new circulars
            new_pdfs = _check_new_circulars_local(mode="live")
            
            if new_pdfs:
                log_message(f"Found {len(new_pdfs)} new circulars")
                
                # Auto-process if enabled
                if MONITORING_CONFIG["auto_process"]:
                    for pdf in new_pdfs:
                        process_new_circular(pdf)
            else:
                log_message("No new circulars found")
            
            # Archive old PDFs
            if MONITORING_CONFIG["archive_old_pdfs"]:
                archive_old_pdfs(days=30)
            
            if not continuous:
                break
            
            log_message(f"⏳ Next check in {interval}s...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        log_message("⛔ Monitoring stopped by user")
    except Exception as e:
        log_message(f"❌ Critical error: {str(e)}")

def run_demo_workflow():
    """Run a demo workflow with sample circulars."""
    log_message("🎬 Running DEMO workflow")
    
    demo_old = "data/circulars/old/demo_old.pdf"
    demo_new = "data/incoming/demo_new.pdf"
    
    # Create demo PDFs if they don't exist
    os.makedirs(os.path.dirname(demo_old), exist_ok=True)
    os.makedirs(os.path.dirname(demo_new), exist_ok=True)
    
    if not os.path.exists(demo_old):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "OLD KYC Policy: Customers must provide PAN and Aadhaar.")
        pdf.output(demo_old)
    
    if not os.path.exists(demo_new):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "NEW KYC Policy: Customers must provide PAN, Aadhaar, and selfie video verification.")
        pdf.output(demo_new)
    
    # Process demo
    result = process_new_circular(demo_new, demo_old)
    
    if result:
        print("\n📊 Demo Results:")
        print(f"  Changes detected: {len(result.get('changes', []))}")
        print(f"  Impacted policies: {len(result.get('impacts', []))}")
        print(f"  Amendments drafted: {len(result.get('amendments', []))}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "live":
            # Run continuous live monitoring
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
            run_live_monitor(interval=interval, continuous=True)
        
        elif command == "once":
            # Run monitoring once
            run_live_monitor(interval=3600, continuous=False)
        
        elif command == "demo":
            # Run demo workflow
            run_demo_workflow()
        
        else:
            print("Usage: python monitor_circulars.py [live|once|demo] [interval_seconds]")
            print("  python monitor_circulars.py live 3600  # Check every hour")
            print("  python monitor_circulars.py once       # Check once")
            print("  python monitor_circulars.py demo       # Run demo workflow")
    else:
        print("Usage: python monitor_circulars.py [live|once|demo] [interval_seconds]")
