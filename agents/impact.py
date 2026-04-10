from langchain_core.tools import tool
from utils.models import ImpactedPolicy
from typing import List
from dataclasses import dataclass, field

# ============================================================================
# ENHANCED POLICY KNOWLEDGE BASE WITH DEPARTMENTS & AFFECTED SYSTEMS
# ============================================================================

@dataclass
class DepartmentRole:
    """Maps departments to policy areas and affected systems"""
    name: str
    responsibilities: List[str]
    affected_systems: List[str]
    priority_level: str  # CRITICAL, HIGH, MEDIUM, LOW

# Department Registry
DEPARTMENTS = {
    "KYC Team": DepartmentRole(
        name="KYC Team",
        responsibilities=["Customer Identification", "Document Verification", "Biometric Capture"],
        affected_systems=["CRM", "Identity Management System", "Document Portal"],
        priority_level="CRITICAL"
    ),
    "AML Compliance": DepartmentRole(
        name="AML Compliance",
        responsibilities=["Screening", "Transaction Monitoring", "Suspicious Activity Reporting"],
        affected_systems=["Screening Engine", "Transaction Monitoring Platform", "FIU Portal"],
        priority_level="CRITICAL"
    ),
    "Operations": DepartmentRole(
        name="Operations",
        responsibilities=["Account Management", "Liquidity Management", "Reserve Management"],
        affected_systems=["Core Banking System", "Treasury Management", "Liquidity Dashboard"],
        priority_level="HIGH"
    ),
    "Legal & Compliance": DepartmentRole(
        name="Legal & Compliance",
        responsibilities=["Policy Updates", "Regulatory Reporting", "Disclosure Management"],
        affected_systems=["Policy Database", "Reporting Engine", "Disclosure Platform"],
        priority_level="HIGH"
    ),
    "Finance": DepartmentRole(
        name="Finance",
        responsibilities=["Interest Rate Compliance", "Ratio Maintenance", "Regulatory Capital"],
        affected_systems=["Accounting System", "Risk Management System", "Ratio Calculator"],
        priority_level="HIGH"
    ),
    "Quality Assurance": DepartmentRole(
        name="Quality Assurance",
        responsibilities=["Policy Compliance Testing", "System Validation", "Training Management"],
        affected_systems=["Test Management System", "Training Platform", "Audit Logs"],
        priority_level="MEDIUM"
    ),
}

# Built-in policy knowledge base — enhanced with impact details
POLICY_KB = [
    {"id": "KYC-1.1", "policy": "KYC Master Policy", "text": "Customer identification procedures for new account opening require government-issued photo ID.", "department": "KYC Team", "entity_impact": "All new customers", "system_impact": ["CRM", "Identity Management System"]},
    {"id": "KYC-1.3", "policy": "KYC Master Policy", "text": "Aadhaar-based eKYC is accepted as valid identification for individual accounts.", "department": "KYC Team", "entity_impact": "Individual account holders", "system_impact": ["CRM", "Biometric System", "eKYC Portal"]},
    {"id": "AML-2.1", "policy": "AML Compliance Policy", "text": "Suspicious transaction reporting must be filed within 7 days of detection to the FIU.", "department": "AML Compliance", "entity_impact": "All transactions", "system_impact": ["Transaction Monitoring Platform", "FIU Portal", "Screening Engine"]},
    {"id": "AML-2.3", "policy": "AML Compliance Policy", "text": "Enhanced due diligence applies to politically exposed persons and high-risk customers.", "department": "AML Compliance", "entity_impact": "PEPs and high-risk segments", "system_impact": ["Screening Engine", "Risk Repository", "Customer Database"]},
    {"id": "OPS-3.1", "policy": "General Banking Operations", "text": "All customer accounts and deposit structures must adhere to the latest RBI guidelines regarding interest rates and classification.", "department": "Operations", "entity_impact": "All customer accounts", "system_impact": ["Core Banking System", "Accounting System", "Rate Engine"]},
    {"id": "OPS-3.2", "policy": "General Banking Operations", "text": "Banks must maintain required Cash Reserve Ratios (CRR) and Statutory Liquidity Ratios (SLR) strictly per regulatory limits.", "department": "Finance", "entity_impact": "Bank reserves and liquidity", "system_impact": ["Treasury Management System", "Liquidity Dashboard", "Ratio Calculator"]},
    {"id": "SEBI-4.1", "policy": "SEBI Disclosure Policy", "text": "Material information must be disclosed to stock exchanges within 24 hours.", "department": "Legal & Compliance", "entity_impact": "Listed entity shareholders", "system_impact": ["Disclosure Platform", "Exchange Portal", "Information Management System"]},
]

# Keywords that map regulatory changes to internal policies
POLICY_KEYWORDS = {
    "KYC Master Policy": ["kyc", "know your customer", "pan", "aadhaar", "identification", "identity", "ekyc", "selfie", "biometric", "customer profile"],
    "AML Compliance Policy": ["aml", "anti-money laundering", "suspicious", "transaction", "reporting", "fiu", "due diligence", "high risk", "pep", "screening"],
    "General Banking Operations": ["account", "customer", "deposit", "interest", "ratio", "liquidity", "reserve", "bank", "rural", "guideline", "credit", "crr", "slr"],
    "SEBI Disclosure Policy": ["sebi", "disclosure", "insider", "trading", "material information", "stock exchange", "listed", "shareholder", "quarterly"],
}

def _keyword_match(text: str) -> List[dict]:
    """Match regulatory change text to relevant internal policies using keyword scoring."""
    text_lower = text.lower()
    matches = []
    for policy_name, keywords in POLICY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            # Find the most relevant chunk from this policy
            policy_chunks = [p for p in POLICY_KB if p["policy"] == policy_name]
            best_chunk = max(policy_chunks, key=lambda p: sum(1 for kw in keywords if kw in p["text"].lower()), default=None)
            if best_chunk:
                matches.append({
                    "policy": policy_name, 
                    "chunk": best_chunk, 
                    "score": score,
                    "department": best_chunk.get("department", "Unknown"),
                    "entity_impact": best_chunk.get("entity_impact", ""),
                    "system_impact": best_chunk.get("system_impact", [])
                })
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:3]

policy_chunks = []  # Legacy - kept for compatibility

@tool
def assess_impact(changes: list) -> List[ImpactedPolicy]:
    """Assess which internal policies are impacted by each regulatory change using keyword matching."""
    impacts = []
    seen = set()

    for change in changes:
        try:
            new_text = getattr(change, 'new_text', '')
            sec_id = getattr(change, 'section_id', 'Unknown')
            if not new_text and isinstance(change, dict):
                new_text = change.get('new_text', '')
                sec_id = change.get('section_id', 'Unknown')
        except Exception as e:
            print(f"Impact agent getattr error: {e}")
            continue

        if not new_text:
            continue

        # Try keyword-based matching (always works, no DB dependency)
        matches = _keyword_match(new_text)
        for m in matches:
            key = (m["policy"], sec_id)
            if key not in seen:
                seen.add(key)
                impacts.append(ImpactedPolicy(
                    policy_name=m["policy"],
                    section_id=sec_id,
                    matched_text=m["chunk"]["text"],
                    relevance_score=float(m["score"]) / 10.0,  # Normalize to 0-1
                    department=m.get("department", "Unknown"),
                    entity_impact=m.get("entity_impact", ""),
                    system_impact=m.get("system_impact", []),
                    affected_roles=_get_affected_roles(m["policy"])
                ))

    impacts.sort(key=lambda x: x.relevance_score, reverse=True)
    return impacts[:10]


def _get_affected_roles(policy_name: str) -> List[str]:
    """Return list of departments affected by this policy."""
    affected = []
    for dept_name, dept in DEPARTMENTS.items():
        # Match department to policy based on keywords
        policy_lower = policy_name.lower()
        if any(keyword in policy_lower for keyword in dept.responsibilities + [dept_name.lower()]):
            affected.append(dept_name)
    
    # Default mapping if no keyword match
    if not affected:
        policy_dept_map = {
            "KYC Master Policy": ["KYC Team", "Legal & Compliance"],
            "AML Compliance Policy": ["AML Compliance", "Legal & Compliance"],
            "General Banking Operations": ["Operations", "Finance", "Quality Assurance"],
            "SEBI Disclosure Policy": ["Legal & Compliance", "Finance"]
        }
        affected = policy_dept_map.get(policy_name, ["Legal & Compliance"])
    
    return affected
