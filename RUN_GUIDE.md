# How to Run RegulaIntel - Complete Guide

## System Overview

RegulaIntel has 4 main components:

```
┌─────────────────────────────────────────────────────────┐
│                  RegulaIntel System                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. Backend API         (FastAPI) - Port 8000           │
│  2. Streamlit Dashboard (Python) - Port 8501            │
│  3. React Frontend      (Vite) - Port 5173              │
│  4. Live Monitor        (Python Script)                  │
│                                                           │
│  Supporting Services:                                    │
│  - Neo4j Database - Port 7474 (optional)                │
│  - ChromaDB - Local vector store                        │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for React frontend)
- **pip & npm** package managers
- **Git** (optional)
- **`.env` file** with API key

---

## ⚙️ Step 1: Setup Environment

### 1.1 Create `.env` File

In the root directory, create `.env`:

```bash
cd d:\Sunhack_Hackathon
```

Create file `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
```

(Get your API key from https://console.groq.com)

### 1.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

**For Windows, it's best to do this in a virtual environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 1.3 Install Node Dependencies (for React frontend)

```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Step 2: Run the Complete System

### **Option A: Run Everything at Once (Recommended)**

**Terminal 1 - Backend API:**
```bash
python api.py
```
✅ API runs on `http://localhost:8000`

**Terminal 2 - Streamlit Dashboard:**
```bash
streamlit run app.py
```
✅ Dashboard opens on `http://localhost:8501`

**Terminal 3 - React Frontend (Optional):**
```bash
cd frontend
npm run dev
```
✅ Frontend runs on `http://localhost:5173`

**Terminal 4 - Live Monitor (Optional):**
```bash
python monitor_circulars.py demo
```

---

### **Option B: Run with Docker Compose (All-in-One)**

```bash
docker compose up -d
```

This starts:
- Neo4j database (optional, for graph visualization)

Then run separately in terminals:

**Backend:**
```bash
python api.py
```

**Dashboard:**
```bash
streamlit run app.py
```

---

### **Option C: Quick Test (Streamlit Only)**

Just the dashboard without API:

```bash
streamlit run app.py
```

📍 Opens: `http://localhost:8501`

---

## 📊 Step 3: Access the Application

### **Streamlit Dashboard** (Recommended for testing)
```
http://localhost:8501
```
- Upload old & new PDFs
- See detected changes
- View impacted policies
- Read drafted amendments
- Download compliance report

### **FastAPI Backend** 
```
http://localhost:8000
```
- REST API endpoints
- Swagger Docs: `http://localhost:8000/docs`

### **React Frontend** (Optional modern UI)
```
http://localhost:5173
```

---

## 🔄 Step 4: Run Individual Components

### **Run Live Monitoring**

```bash
# Demo mode (local PDFs)
python monitor_circulars.py demo

# Live mode - check once
python monitor_circulars.py once

# Live mode - continuous (every hour)
python monitor_circulars.py live 3600
```

### **Run Tests**

```bash
# Test setup
python test_setup.py

# Test workflow
python test_workflow_script.py
```

### **Process PDFs via API**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "old_pdf=@old_doc.pdf" \
  -F "new_pdf=@new_doc.pdf"
```

---

## 📁 Step 5: Prepare Sample Data

### **Add PDFs for Testing**

1. **Create demo PDFs:**
```bash
# Place your PDFs here for demo mode
mkdir -p data/incoming
# Add your PDF files here
```

2. **Or use test script to generate samples:**
```bash
python test_setup.py
```

### **Check Data Directories**

```
data/
├── incoming/           ← Drop PDFs here for monitoring
├── circulars/
│   ├── old/           ← Archived circulars
│   └── new/           ← Recent circulars
├── internal/          ← Internal policies
│   ├── kyc_policy.txt
│   └── policies.json
└── monitoring.log     ← Monitor logs
```

---

## 🎯 Typical Workflow

### **Via Streamlit Dashboard (Easiest)**

1. **Start Dashboard:**
   ```bash
   streamlit run app.py
   ```

2. **Upload Files:**
   - Upload `old_circular.pdf` (baseline)
   - Upload `new_circular.pdf` (latest)

3. **View Results:**
   - ✅ Changes detected
   - ✅ Impacted policies identified
   - ✅ Amendments auto-drafted
   - ✅ Download PDF report

### **Via API (Programmatic)**

1. **Start API:**
   ```bash
   python api.py
   ```

2. **Send Request:**
   ```bash
   curl -X POST http://localhost:8000/api/analyze \
     -F "old_pdf=@baseline.pdf" \
     -F "new_pdf=@updated.pdf"
   ```

3. **Get Response:**
   ```json
   {
     "changes": [...],
     "impacts": [...],
     "amendments": [...]
   }
   ```

### **Via Live Monitor (Automated)**

1. **Start Monitoring:**
   ```bash
   python monitor_circulars.py live 3600
   ```

2. **System Automatically:**
   - Fetches new circulars (RBI/SEBI/MCA)
   - Downloads PDFs
   - Processes them through workflow
   - Generates reports

---

## ⚡ Quick Commands Cheatsheet

| Task | Command |
|------|---------|
| **Streamlit Dashboard** | `streamlit run app.py` |
| **FastAPI Backend** | `python api.py` |
| **React Frontend** | `cd frontend && npm run dev` |
| **Live Monitor (one-time)** | `python monitor_circulars.py once` |
| **Live Monitor (continuous)** | `python monitor_circulars.py live 3600` |
| **Demo Mode** | `python monitor_circulars.py demo` |
| **Run Tests** | `python test_setup.py` |
| **View API Docs** | Open `http://localhost:8000/docs` |
| **Check Monitoring** | `GET http://localhost:8000/api/monitor/status` |

---

## 🐛 Troubleshooting

### **Issue: "ModuleNotFoundError: No module named 'agents'"**

**Solution:**
```bash
# Make sure you're in the root directory
cd d:\Sunhack_Hackathon

# Verify __init__.py exists in agents folder
ls agents/__init__.py

# Reinstall dependencies
pip install -r requirements.txt
```

### **Issue: "No GROQ_API_KEY found"**

**Solution:**
1. Create `.env` file with your key
2. Verify it's in root directory
3. Restart the application
4. Check:
   ```bash
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GROQ_API_KEY'))"
   ```

### **Issue: Port 8000 already in use**

**Solution:**
```bash
# Use different port
python api.py --port 8001

# Or kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### **Issue: PDFs not found in monitoring**

**Solution:**
1. Verify PDFs are in `data/incoming/`
2. Check permissions (make sure folder is writable)
3. For live mode, verify internet connection
4. Check logs: `cat data/monitoring.log`

### **Issue: Streamlit app not loading**

**Solution:**
```bash
# Clear Streamlit cache
streamlit cache clear

# Run with verbose output
streamlit run app.py --logger.level=debug
```

---

## 📊 Expected Output

### **From Streamlit Dashboard**

When processing PDFs, you should see:

```
✅ PDF Ingest Complete
   - Old document: 5 sections
   - New document: 6 sections

🔍 Changes Detected: 2
   - Section KYC-1.1: Modified
   - Section AML-2.3: New

📋 Impacted Policies: 3
   - KYC Master Policy
   - AML Compliance Policy
   - General Banking Operations

✍️ Amendments Drafted: 2
   - Update KYC section on Aadhaar
   - Add selfie verification requirement

📥 Report Generated
   → compliance_report.pdf
```

---

## 🔧 Advanced Configuration

### **Customize Monitoring Interval**

Edit `monitor_circulars.py`:

```python
MONITORING_CONFIG = {
    "check_interval": 1800,  # 30 minutes instead of 1 hour
    "auto_process": True,
    "archive_old_pdfs": True,
}
```

### **Enable Specific Regulatory Sources**

Edit `agents/monitor.py`:

```python
# Comment out to disable
RBI_FEEDS = { ... }       # ← Set to {} to disable
SEBI_URLS = { ... }       # ← Set to {} to disable
MCA_URLS = { ... }        # ← Set to {} to disable
```

### **Custom Policy Mappings**

Edit `agents/impact.py`:

```python
POLICY_KEYWORDS = {
    "Your Policy Name": ["keyword1", "keyword2"],
    ...
}
```

---

## 📚 Full Component Details

| Component | Port | Purpose | Command |
|-----------|------|---------|---------|
| **Streamlit** | 8501 | Web Dashboard | `streamlit run app.py` |
| **FastAPI** | 8000 | REST API | `python api.py` |
| **React (Vite)** | 5173 | Modern Frontend | `npm run dev` |
| **Neo4j** | 7474 | Graph DB (optional) | `docker compose up neo4j` |

---

## ✅ Validation Checklist

- [ ] `.env` file created with GROQ_API_KEY
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Node dependencies installed: `npm install` (if using React)
- [ ] Sample PDFs placed in `data/incoming/` (optional)
- [ ] Can access `http://localhost:8501` (Streamlit)
- [ ] Can access `http://localhost:8000/docs` (API)
- [ ] Test workflow completes without errors

---

## 🎬 Start Here (5 Minutes)

```bash
# 1. Navigate to project
cd d:\Sunhack_Hackathon

# 2. Activate Python env (Windows)
venv\Scripts\activate

# 3. Start dashboard
streamlit run app.py

# 4. Open browser to http://localhost:8501
# 5. Upload sample PDFs and test!
```

---

For more details, see:
- [LIVE_MONITORING.md](LIVE_MONITORING.md) - Live monitoring setup
- [README.md](README.md) - System overview
- API Docs: `http://localhost:8000/docs` - REST endpoints
