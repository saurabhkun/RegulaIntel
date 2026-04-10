# Live Regulatory Monitoring Setup Guide

## Overview
RegulaIntel can now monitor real regulatory circulars from **RBI**, **SEBI**, and **MCA** and automatically process them through the compliance workflow.

## Two Modes

### 1. **DEMO Mode** (Local Testing)
- Checks local `data/incoming/` folder for PDFs
- No external dependencies
- Perfect for testing

### 2. **LIVE Mode** (Production)
- Fetches real circulars from:
  - **RBI**: RSS feeds for notifications & press releases
  - **SEBI**: Web scraping of circulars page
  - **MCA**: Web scraping of notification center
- Automatically downloads PDFs
- Tracks changes with timestamp

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

The key dependencies added are:
- `feedparser` - Parse RSS feeds from RBI
- `lxml` - XML parsing for feeds
- `requests` - Download PDFs
- `beautifulsoup4` - Web scraping (already included)

### 2. Verify Installation
```bash
python -c "import feedparser; print('✅ feedparser installed')"
```

## Usage

### Option A: Command Line Monitoring

#### Check Once (Demo)
```bash
python monitor_circulars.py demo
```

#### Check Once (Live)
```bash
python monitor_circulars.py once
```

#### Continuous Monitoring (Every Hour)
```bash
python monitor_circulars.py live 3600
```

#### Custom Interval (Every 30 minutes)
```bash
python monitor_circulars.py live 1800
```

### Option B: Via API Endpoints

#### Start Live Monitoring
```bash
POST http://localhost:8000/api/monitor/start/live
```

#### Check Once
```bash
POST http://localhost:8000/api/monitor/check-once/live
```

#### Check Monitoring Status
```bash
GET http://localhost:8000/api/monitor/status
```

#### Get Incoming Circulars
```bash
GET http://localhost:8000/api/monitor/incoming
```

### Option C: Using Docker Compose

Add this service to `docker-compose.yml`:
```yaml
monitor:
  build: .
  command: python monitor_circulars.py live 3600
  environment:
    - GROQ_API_KEY=${GROQ_API_KEY}
  volumes:
    - ./data:/Sunhack_Hackathon/data
  depends_on:
    - api
```

Run:
```bash
docker-compose up monitor
```

## Workflow

```
┌─────────────────────────────────────────┐
│   Check New Circulars                   │
│   (RBI/SEBI/MCA)                        │
└──────────────┬──────────────────────────┘
               │
               ├─→ Fetch RSS/Web Pages
               ├─→ Scrape PDF Links
               ├─→ Download PDFs
               └─→ Save to data/incoming/
                   │
                   ▼
         ┌─────────────────────┐
         │  Auto-Process       │
         │  (if enabled)       │
         └─────────────────────┘
                   │
                   ├─→ Ingest PDFs
                   ├─→ Compute Diff
                   ├─→ Assess Impact
                   ├─→ Draft Amendments
                   └─→ Generate Report
```

## Configuration

Edit `monitor_circulars.py` to customize:

```python
MONITORING_CONFIG = {
    "check_interval": 3600,      # Check every hour
    "auto_process": True,         # Auto-process new circulars
    "archive_old_pdfs": True,     # Archive old files
    "log_file": "data/monitoring.log"
}
```

## Data Structure

### Downloaded Circulars
```
data/incoming/
  ├── RBI_notifications_0_20260410_120000.pdf
  ├── SEBI_circulars_1_20260410_120015.pdf
  └── MCA_notifications_2_20260410_120030.pdf
```

### Processing Logs
```
data/monitoring.log
  [2026-04-10 12:00:00] 🚀 Starting Live Regulatory Monitoring
  [2026-04-10 12:00:00] Monitoring: RBI, SEBI, MCA
  [2026-04-10 12:00:05] 🔄 Checking for new circulars...
  [2026-04-10 12:00:10] Found 3 new circulars
  [2026-04-10 12:00:15] ✅ Downloaded 3 PDFs
```

### Last Check Timestamp
```json
{
  "last_checked": "2026-04-10T12:00:15.123456"
}
```

## Troubleshooting

### Issue: No circulars found even in live mode

**Solution:**
- Verify internet connection
- Check if RSS feeds are accessible:
  ```bash
  python -c "import feedparser; feed = feedparser.parse('https://www.rbi.org.in/english/RSS.aspx?ID=165'); print(f'Entries: {len(feed.entries)}')"
  ```
- Check browser: Visit the URLs manually to verify data exists

### Issue: PDF download fails

**Solution:**
- Some PDFs may require authentication
- Check `data/monitoring.log` for specific errors
- Verify SEBI/MCA URLs are still valid (they change occasionally)

### Issue: Memory error with large PDFs

**Solution:**
```python
# In monitor_circulars.py, limit PDF size
if response.headers.get('content-length', 0) > 50_000_000:  # 50MB limit
    continue
```

### Issue: Too many API calls / Rate limiting

**Solution:**
- Increase `check_interval` in `MONITORING_CONFIG`
- Implement backoff strategy in `monitor.py`

## Testing

### Test Demo Mode
```bash
python monitor_circulars.py demo
```

Creates sample PDFs and processes them.

### Test Live Mode (Single Check)
```bash
python monitor_circulars.py once
```

Makes one call to RBI/SEBI/MCA without continuous loop.

### Test with Custom Baseline
Edit `monitor_circulars.py`:
```python
result = process_new_circular(
    pdf_path,
    old_baseline="path/to/baseline.pdf"
)
```

## Advanced: Docker Container

### Build Image
```bash
docker build -t regula-intel-monitor .
```

### Run Continuous Container
```bash
docker run -d \
  --name regula-monitor \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  -v $(pwd)/data:/app/data \
  regula-intel-monitor \
  python monitor_circulars.py live 3600
```

### View Logs
```bash
docker logs -f regula-monitor
```

## Real-World Sources

### RBI (Reserve Bank of India)
- **Notifications**: `https://www.rbi.org.in/english/RSS.aspx?ID=165`
- **Press Releases**: `https://www.rbi.org.in/english/RSS.aspx?ID=35`
- **Circulars Portal**: `https://www.rbi.org.in/`

### SEBI (Securities and Exchange Board of India)
- **Circulars**: `https://www.sebi.gov.in/sebiweb/other/OtherMainAction.do?doRecognised=yes&intmnuid=13`
- **PDF Database**: Most pages link to PDF downloads

### MCA (Ministry of Corporate Affairs)
- **Notifications**: `https://www.mca.gov.in/content/dam/mca/notification/`
- **Latest Updates**: Published regularly

## Next Steps

1. **Customize Policy Keywords**: Update `POLICY_KEYWORDS` in [agents/impact.py](agents/impact.py) with your internal policy mappings
2. **Add Webhook Integration**: Send alerts when critical circulars are detected
3. **Setup Notifications**: Email/Slack alerts on new amendments
4. **Database Backup**: Archive processed circulars in database

---

For questions, check the main [README.md](../README.md)
