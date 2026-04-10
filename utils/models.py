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

class Amendment(BaseModel):
    policy_name: str
    section_id: str
    current_text: str
    proposed_text: str
    justification: str
    source_citation: str  # "Page X, Section Y"

class StructuredDocument(BaseModel):
    sections: List[dict]  # {'id': str, 'text': str, 'page': int}
    metadata: dict

