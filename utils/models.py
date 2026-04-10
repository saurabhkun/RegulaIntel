from pydantic import BaseModel
from typing import List
from dataclasses import dataclass

@dataclass
class Change:
    section_id: str
    old_text: str
    new_text: str
    similarity_score: float
    confidence: str  # HIGH/MEDIUM/LOW
    page_number: int
    severity: str = "LOW"

class ImpactedPolicy(BaseModel):
    policy_name: str
    section_id: str
    matched_text: str
    relevance_score: float
    department: str = "Unknown"  # NEW: Which department is affected
    entity_impact: str = ""  # NEW: Who/what is affected (e.g., "All new customers")
    system_impact: List[str] = []  # NEW: Which systems need updates
    affected_roles: List[str] = []  # NEW: List of departments/teams affected

class Amendment(BaseModel):
    policy_name: str
    section_id: str
    current_text: str
    proposed_text: str
    justification: str
    source_citation: str  # "Page X, Section Y"
    department: str = "Unknown"  # NEW: Department responsible
    implementation_effort: str = "MEDIUM"  # NEW: LOW/MEDIUM/HIGH/CRITICAL
    affected_systems: List[str] = []  # NEW: Systems requiring updates
    testing_required: bool = True  # NEW: Whether QA testing needed

class StructuredDocument(BaseModel):
    sections: List[dict]  # {'id': str, 'text': str, 'page': int}
    metadata: dict

