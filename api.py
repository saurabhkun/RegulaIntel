from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from agents.workflow import graph as workflow_graph
from agents.monitor import check_new_circulars
from utils.report_generator import ReportGenerator
from pydantic import BaseModel
import os
import tempfile
import uvicorn
import threading

app = FastAPI(title="RegulaIntel API")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
async def analyze_circulars(old_pdf: UploadFile = File(...), new_pdf: UploadFile = File(...)):
    try:
        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as old_tmp:
            old_tmp.write(await old_pdf.read())
            old_path = old_tmp.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as new_tmp:
            new_tmp.write(await new_pdf.read())
            new_path = new_tmp.name
            
        # Run the workflow
        result = workflow_graph.invoke({"old_pdf": old_path, "new_pdf": new_path})
        
        # Clean up temp files
        os.unlink(old_path)
        os.unlink(new_path)
        
        # The result dict from LangGraph graph contains Pydantic objects/dataclasses.
        # We need to serialize them to basic dicts for JSON
        def serialize(obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)

        safe_changes = [serialize(c) for c in result.get('changes', [])]
        safe_impacts = [serialize(i) for i in result.get('impacts', [])]
        safe_amends = [serialize(a) for a in result.get('amendments', [])]
            
        return JSONResponse(content={
            "changes": safe_changes,
            "impacts": safe_impacts,
            "amendments": safe_amends
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.post("/api/analyze/live")
async def analyze_live_circular():
    try:
        old_path = "data/circulars/old/demo_old.pdf"
        
        # Grab the absolute newest downloaded live PDF
        import glob
        pdfs = glob.glob("data/incoming/*.pdf")
        if not pdfs:
            return JSONResponse(status_code=404, content={"message": "No live circulars downloaded yet. Run scraper first."})
        
        new_path = max(pdfs, key=os.path.getmtime)
            
        # Run the workflow
        result = workflow_graph.invoke({"old_pdf": old_path, "new_pdf": new_path})
        
        def serialize(obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)

        safe_changes = [serialize(c) for c in result.get('changes', [])]
        safe_impacts = [serialize(i) for i in result.get('impacts', [])]
        safe_amends = [serialize(a) for a in result.get('amendments', [])]
            
        return JSONResponse(content={
            "changes": safe_changes,
            "impacts": safe_impacts,
            "amendments": safe_amends
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})




@app.post("/api/report")
async def generate_report(data: dict):
    try:
        # we expect raw dicts for changes and amendments in data
        changes = data.get('changes', [])
        amendments = data.get('amendments', [])
        
        # ReportGenerator expects objects with gettattr, so we mock them or let report_generator use dicts.
        # Wait, report_generator uses `getattr(c, 'severity', 'LOW')`
        # We can wrap dicts in simple mocked objects.
        class MockObj:
            def __init__(self, d):
                self.__dict__.update(d)
                
        c_objs = [MockObj(c) for c in changes]
        a_objs = [MockObj(a) for a in amendments]
        
        rg = ReportGenerator()
        report_path = "compliance_report.pdf"
        rg.generate_report(c_objs, a_objs, report_path)
        
        return FileResponse(report_path, filename="RegulaIntel_Report.pdf", media_type="application/pdf")
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# Live Monitoring Endpoints
monitoring_thread = None

@app.get("/api/monitor/status")
async def monitor_status():
    """Get current monitoring status."""
    if os.path.exists("data/last_checked.json"):
        import json
        with open("data/last_checked.json", 'r') as f:
            data = json.load(f)
            return JSONResponse(content={
                "status": "active",
                "last_checked": data.get("last_checked"),
                "monitoring_active": monitoring_thread is not None and monitoring_thread.is_alive()
            })
    
    return JSONResponse(content={
        "status": "inactive",
        "last_checked": None,
        "monitoring_active": False
    })


@app.post("/api/monitor/start/{mode}")
async def start_monitoring(mode: str = "demo"):
    """
    Start monitoring for new circulars.
    
    Args:
        mode: "demo" (local) or "live" (RBI/SEBI/MCA)
    """
    global monitoring_thread
    
    if monitoring_thread and monitoring_thread.is_alive():
        return JSONResponse(content={"message": "Monitoring already running"})
    
    def run_monitor():
        try:
            print(f"🚀 Starting {mode} monitoring...")
            pdfs = check_new_circulars.invoke({"mode": mode})
            print(f"Found {len(pdfs)} circulars: {pdfs}")
            return pdfs
        except Exception as e:
            print(f"Error in monitoring: {e}")
            return []
    
    monitoring_thread = threading.Thread(target=run_monitor, daemon=True)
    monitoring_thread.start()
    
    return JSONResponse(content={
        "message": f"Started {mode} monitoring",
        "mode": mode
    })


@app.get("/api/monitor/check-once/{mode}")
async def check_once(mode: str = "demo"):
    """Check for new circulars immediately (without continuous monitoring)."""
    try:
        pdfs = check_new_circulars.invoke({"mode": mode})
        
        return JSONResponse(content={
            "found": len(pdfs),
            "circulars": [os.path.basename(p) for p in pdfs],
            "mode": mode
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "mode": mode
        })


@app.get("/api/monitor/incoming")
async def get_incoming_circulars():
    """Get list of incoming circulars in demo folder."""
    try:
        import glob
        incoming_dir = "data/incoming"
        os.makedirs(incoming_dir, exist_ok=True)
        
        pdfs = glob.glob(os.path.join(incoming_dir, "*.pdf"))
        
        return JSONResponse(content={
            "count": len(pdfs),
            "files": [os.path.basename(p) for p in pdfs]
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
