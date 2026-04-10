from langchain_core.tools import tool
from langchain_groq import ChatGroq
from utils.models import Amendment
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List
import os

class ListAmendment(BaseModel):
    amendments: List[Amendment] = Field(description="List of drafted amendments")

@tool
def draft_amendments(impacts: list, changes: list) -> List[Amendment]:
    """Generate structured amendment drafts with citations."""
    # Lazy-load: always re-read the API key at call time (not import time)
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key == "dummy":
        print("Drafter: No valid GROQ_API_KEY found, skipping LLM drafting.")
        return []
    
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=api_key)
    except Exception as e:
        print(f"Drafter: Failed to initialize LLM: {e}")
        return []
    
    impacts_str = "\n".join([f"Policy: {i.policy_name}, Section: {i.section_id}, Text: {i.matched_text}" for i in impacts[:3]])
    
    # Handle dict/model formats
    def safe_get(c, key, default=''):
        return getattr(c, key, default) if hasattr(c, key) else (c.get(key, default) if isinstance(c, dict) else default)
        
    changes_str = "\n".join([f"ID: {safe_get(c, 'section_id')}, Old: {safe_get(c, 'old_text')}, New: {safe_get(c, 'new_text')}" for c in changes[:3]])

    prompt = f"""
    You are a Senior Regulatory Compliance Analyst. Draft the necessary amendments to internal policies.
    IMPACTED POLICIES:
    {impacts_str}
    
    REGULATORY CHANGES:
    {changes_str}
    """
    
    try:
        chain = llm.with_structured_output(ListAmendment)
        result = chain.invoke(prompt)
        for a in result.amendments:
            a.source_citation = "Mapped from change sections"
        print(f"Drafter: Successfully drafted {len(result.amendments)} amendments.")
        return result.amendments
    except Exception as e:
        print(f"Drafter error: {e}")
        return []
