from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from utils.models import Change, Amendment
import operator
from .supervisor import supervisor
from .ingest import ingest_pdf
from .diff import compute_diff
from .impact import assess_impact
from .drafter import draft_amendments

class AgentState(TypedDict):
    old_pdf: str
    new_pdf: str
    old_doc: List[dict]
    new_doc: List[dict]
    changes: Annotated[List[Change], operator.add]
    impacts: Annotated[List, operator.add]
    amendments: Annotated[List[Amendment], operator.add]
    next: str

def ingest_node(state):
    return {
        "old_doc": ingest_pdf.invoke({"pdf_path": state['old_pdf']}),
        "new_doc": ingest_pdf.invoke({"pdf_path": state['new_pdf']})
    }

def diff_node(state):
    changes = compute_diff.invoke({"old_sections": state["old_doc"], "new_sections": state["new_doc"]})
    return {"changes": changes, "next": "impact" if changes else END}

def impact_node(state):
    impacts = assess_impact.invoke({"changes": state["changes"]})
    return {"impacts": impacts}

def drafter_node(state):
    # Always call the drafter as long as there are changes — impacts may be empty
    changes = state["changes"]
    impacts = state.get("impacts", [])
    if not changes:
        return {"amendments": []}
    amendments = draft_amendments.invoke({"impacts": impacts[:5], "changes": changes[:5]})
    return {"amendments": amendments}

from langchain_core.messages import HumanMessage

def supervisor_node(state):
    global supervisor
    if supervisor is None:
        return state  # Skip supervisor if no API key
    # Simple supervisor for final review
    msg = f"Summarize impacts ({len(state['impacts'])}) and amendments ({len(state['amendments'])}) for compliance report."
    try:
        result = supervisor.invoke({"messages": [HumanMessage(content=msg)]})
    except:
        result = None
    return state  # No change for MVP



workflow = StateGraph(AgentState)
workflow.add_node("ingest", ingest_node)
workflow.add_node("diff", diff_node)
workflow.add_node("impact", impact_node)
workflow.add_node("drafter", drafter_node)
workflow.add_node("supervisor", supervisor_node)

workflow.set_entry_point("ingest")
workflow.add_edge("ingest", "diff")

workflow.add_conditional_edges(
    "diff",
    lambda state: "impact" if state["changes"] else END,
    {"impact": "impact", END: END}
)
workflow.add_edge("impact", "drafter")
workflow.add_edge("drafter", "supervisor")
workflow.add_edge("supervisor", END)

graph = workflow.compile()

