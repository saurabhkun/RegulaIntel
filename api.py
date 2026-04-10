from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from agents.workflow import graph as workflow_graph
from agents.monitor import check_new_circulars
from agents.executor import execute_amendments
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


# ============================================================================
# ENHANCED IMPACT MAPPING ENDPOINTS
# ============================================================================

@app.post("/api/impact/detailed")
async def get_detailed_impact(amendments: list):
    """
    Get comprehensive impact analysis for amendments:
    - Which departments are affected
    - Which systems need updates
    - Who needs to be notified
    - Implementation effort
    - Testing requirements
    """
    try:
        impact_summary = {
            "total_amendments": len(amendments),
            "departments_affected": {},
            "systems_affected": {},
            "implementation_effort": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "notification_matrix": {},
            "testing_requirements": [],
            "affected_roles": set()
        }
        
        for amend in amendments:
            # Aggregate department impacts
            dept = amend.get("department", "Unknown")
            if dept not in impact_summary["departments_affected"]:
                impact_summary["departments_affected"][dept] = []
            impact_summary["departments_affected"][dept].append({
                "policy": amend.get("policy_name"),
                "section": amend.get("section_id")
            })
            
            # Aggregate system impacts
            for system in amend.get("affected_systems", []):
                if system not in impact_summary["systems_affected"]:
                    impact_summary["systems_affected"][system] = 0
                impact_summary["systems_affected"][system] += 1
            
            # Track implementation effort
            effort = amend.get("implementation_effort", "MEDIUM")
            impact_summary["implementation_effort"][effort] += 1
            
            # Track testing needs
            if amend.get("testing_required", True):
                impact_summary["testing_requirements"].append({
                    "policy": amend.get("policy_name"),
                    "section": amend.get("section_id"),
                    "systems": amend.get("affected_systems", [])
                })
            
            # Collect affected roles
            for role in amend.get("affected_roles", []):
                impact_summary["affected_roles"].add(role)
        
        # Convert set to list for JSON serialization
        impact_summary["affected_roles"] = list(impact_summary["affected_roles"])
        
        return JSONResponse(content=impact_summary)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/api/impact/department/{dept_name}")
async def get_department_impact(dept_name: str):
    """Get impact analysis specific to a department"""
    try:
        # This would need amendments in a database or session
        # For now return the department's mandate and affected policies
        from agents.impact import DEPARTMENTS
        
        if dept_name in DEPARTMENTS:
            dept = DEPARTMENTS[dept_name]
            return JSONResponse(content={
                "department": dept_name,
                "responsibilities": dept.responsibilities,
                "affected_systems": dept.affected_systems,
                "priority_level": dept.priority_level,
                "action_items": f"Review {len(dept.responsibilities)} areas of responsibility"
            })
        else:
            return JSONResponse(status_code=404, content={"message": "Department not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# ============================================================================
# AUTO COMPLIANCE EXECUTION ENDPOINTS
# ============================================================================

@app.post("/api/compliance/execute")
async def auto_execute_compliance(amendments: list, dry_run: bool = False):
    """
    Execute amendments automatically:
    - Apply to policy database
    - Update system configs
    - Create audit trail
    - Send notifications
    
    Args:
        amendments: List of Amendment objects to execute
        dry_run: If true, simulate execution without actual changes
    """
    try:
        if dry_run:
            # Simulate execution plan without applying changes
            from agents.executor import _create_execution_plan
            plan = _create_execution_plan(amendments)
            return JSONResponse(content={
                "mode": "DRY_RUN",
                "plan_id": plan.plan_id,
                "total_amendments": len(amendments),
                "execution_order": plan.execution_order,
                "critical_path": plan.critical_path,
                "parallel_safe": plan.parallel_safe,
                "estimated_duration_seconds": plan.estimated_duration_seconds,
                "status": "SIMULATED"
            })
        else:
            # Execute for real
            result = execute_amendments.invoke([amend for amend in amendments])
            return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/api/compliance/execution-logs")
async def get_execution_logs():
    """Get list of all execution logs"""
    try:
        import json
        import glob
        
        log_files = glob.glob("data/execution_logs/*_summary.json")
        logs = []
        
        for log_file in sorted(log_files, reverse=True)[:10]:  # Last 10
            with open(log_file, 'r') as f:
                logs.append(json.load(f))
        
        return JSONResponse(content={"execution_logs": logs})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/api/compliance/audit-trail")
async def get_audit_trail():
    """Get complete audit trail of all executed amendments"""
    try:
        import json
        
        if os.path.exists("data/execution_logs/audit_trail.json"):
            with open("data/execution_logs/audit_trail.json", 'r') as f:
                audit_log = json.load(f)
            return JSONResponse(content={"audit_entries": audit_log})
        else:
            return JSONResponse(content={"audit_entries": []})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/api/compliance/notifications")
async def get_sent_notifications():
    """Get list of notifications sent to departments"""
    try:
        import json
        
        if os.path.exists("data/execution_logs/notifications.json"):
            with open("data/execution_logs/notifications.json", 'r') as f:
                notifications = json.load(f)
            return JSONResponse(content={"notifications": notifications})
        else:
            return JSONResponse(content={"notifications": []})
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
