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
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from db.database import get_db_connection
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class ChatRequest(BaseModel):
    session_id: str
    message: str

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
        from typing import Dict, Any
        impact_summary: Dict[str, Any] = {
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
            if dept not in impact_summary["departments_affected"]: # type: ignore
                impact_summary["departments_affected"][dept] = [] # type: ignore
            impact_summary["departments_affected"][dept].append({ # type: ignore
                "policy": amend.get("policy_name"),
                "section": amend.get("section_id")
            })
            
            # Aggregate system impacts
            for system in amend.get("affected_systems", []):
                if system not in impact_summary["systems_affected"]: # type: ignore
                    impact_summary["systems_affected"][system] = 0 # type: ignore
                impact_summary["systems_affected"][system] += 1 # type: ignore
            
            # Track implementation effort
            effort = amend.get("implementation_effort", "MEDIUM")
            impact_summary["implementation_effort"][effort] += 1 # type: ignore
            
            # Track testing needs
            if amend.get("testing_required", True):
                impact_summary["testing_requirements"].append({ # type: ignore
                    "policy": amend.get("policy_name"),
                    "section": amend.get("section_id"),
                    "systems": amend.get("affected_systems", [])
                })
            
            # Collect affected roles
            for role in amend.get("affected_roles", []):
                impact_summary["affected_roles"].add(role) # type: ignore
        
        # Convert set to list for JSON serialization
        impact_summary["affected_roles"] = list(impact_summary["affected_roles"]) # type: ignore
        
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
        
        for log_file in sorted(log_files, reverse=True)[:10]:  # type: ignore
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

# ============================================================================
# RAG CHAT HISTORY ENGINE
# ============================================================================

@app.post("/api/chat/session")
async def create_chat_session():
    """Create a new chat session."""
    try:
        session_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        conn.commit()
        conn.close()
        return JSONResponse(content={"session_id": session_id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/api/chat/sessions")
async def get_chat_sessions():
    """Get all past chat sessions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.session_id, s.created_at, 
                   (SELECT content FROM messages m WHERE m.session_id = s.session_id ORDER BY timestamp ASC LIMIT 1) as title
            FROM sessions s
            ORDER BY s.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for r in rows:
            sessions.append({
                "session_id": r["session_id"],
                "created_at": r["created_at"],
                "title": r["title"][:50] + "..." if r["title"] and len(r["title"]) > 50 else (r["title"] or "New Chat")
            })
        return JSONResponse(content={"sessions": sessions})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/api/chat/messages/{session_id}")
async def get_chat_messages(session_id: str):
    """Retrieve history for a specific session."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, content, circular_refs FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        rows = cursor.fetchall()
        conn.close()
        
        messages = [{"role": r["role"], "content": r["content"], "circular_refs": r["circular_refs"]} for r in rows]
        return JSONResponse(content={"messages": messages})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.post("/api/chat")
async def process_chat(request: ChatRequest):
    """Process a user message with 6-message RAG context."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Save user message
        cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", 
                       (request.session_id, "user", request.message))
        conn.commit()
        
        # 2. Retrieve last 6 messages
        cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 6", 
                       (request.session_id,))
        history_rows = cursor.fetchall()
        
        # Reverse to chronological order
        history_rows.reverse()
        
        # 3. Construct LangChain messages
        messages = [
            SystemMessage(content="You are RegulaIntel, an expert AI on Indian Financial Compliance. IMPORTANT: Keep your responses EXTREMELY concise (max 3-4 bullet points). Always summarize. Your goal is to provide a clean, high-impact answer that fits on a single mobile/desktop screen for demonstration purposes.")
        ]
        
        for r in history_rows:
            if r["role"] == "user":
                messages.append(HumanMessage(content=r["content"]))
            elif r["role"] == "ai":
                messages.append(AIMessage(content=r["content"]))
                
        # 4. Invoke LLM (Mocked or actual if GROQ_API_KEY is present)
        import os
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.2, groq_api_key=api_key)
            ai_response = llm.invoke(messages).content
        else:
            # Fallback for hackathon demo if key drops
            ai_response = "As an AI Compliance Sentinel, I acknowledge your query. However, my Language Model routing is currently offline (Missing API Key). My core directive confirms that under Section 45-IA, operational frameworks require strict auditing."

        # Simulate a circular reference tag for the mock requirement
        refs = "RBI/2024-25/112 (KYC Master Direction)" if "kyc" in request.message.lower() else "SEBI/HO/MIRSD/2024/09"
        
        # 5. Save AI response
        cursor.execute("INSERT INTO messages (session_id, role, content, circular_refs) VALUES (?, ?, ?, ?)", 
                       (request.session_id, "ai", ai_response, refs))
        conn.commit()
        conn.close()
        
        return JSONResponse(content={
            "response": ai_response,
            "circular_refs": refs
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

# ============================================================================
# HISTORICAL CIRCULAR TRACKING
# ============================================================================

@app.get("/api/history/circulars")
async def get_circular_history():
    """Retrieve all circulars and their historical versions."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT circular_id, source, version_number, ingested_at, file_path 
            FROM circular_versions 
            ORDER BY circular_id, version_number DESC
        """)
        rows = c.fetchall()
        conn.close()
        
        history_map = {}
        for r in rows:
            cid = r["circular_id"]
            if cid not in history_map:
                history_map[cid] = {"circular_id": cid, "source": r["source"], "versions": []}
            history_map[cid]["versions"].append({
                "version_number": r["version_number"],
                "ingested_at": r["ingested_at"],
                "file_path": r["file_path"]
            })
            
        return JSONResponse(content={"circulars": list(history_map.values())})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/api/history/diff/{circular_id}")
async def invoke_historical_diff(circular_id: str, v1: int, v2: int):
    """Run the diff agent between two historical versions of the same circular."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT file_path FROM circular_versions WHERE circular_id = ? AND version_number = ?", (circular_id, v1))
        p1 = c.fetchone()
        c.execute("SELECT file_path FROM circular_versions WHERE circular_id = ? AND version_number = ?", (circular_id, v2))
        p2 = c.fetchone()
        conn.close()
        
        if not p1 or not p2:
            return JSONResponse(status_code=404, content={"message": "Could not locate the requested versions."})
            
        # Push through standard graph invocation
        from agents.workflow import graph as workflow_graph
        result = workflow_graph.invoke({"old_pdf": p1["file_path"], "new_pdf": p2["file_path"]})
        
        def serialize(obj):
            if hasattr(obj, 'model_dump'): return obj.model_dump()
            elif hasattr(obj, '__dict__'): return obj.__dict__
            return str(obj)

        safe_changes = [serialize(c) for c in result.get('changes', [])]
        return JSONResponse(content={"diff_report": safe_changes})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
