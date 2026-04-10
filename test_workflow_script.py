import sys
import traceback
import asyncio
from pathlib import Path

print("Starting workflow test")
try:
    from agents.workflow import graph as workflow_graph
    state = {
        "old_pdf": "data/circulars/old/demo_old.pdf",
        "new_pdf": "data/circulars/new/demo_new.pdf"
    }
    # Create the internal collection to avoid missing chunks if running from scratch
    from utils.vector_store import index_policies
    index_policies()
    
    result = workflow_graph.invoke(state)
    print("Success. Elements in result:")
    print("Changes:", len(result.get("changes", [])))
    print("Impacts:", len(result.get("impacts", [])))
    print("Amendments:", len(result.get("amendments", [])))
except Exception as e:
    print("Workflow failed!")
    traceback.print_exc()
    sys.exit(1)
