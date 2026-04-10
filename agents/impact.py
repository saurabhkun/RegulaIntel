from langchain_core.tools import tool
from utils.models import ImpactedPolicy
from typing import List

# Built-in policy knowledge base — no ChromaDB needed
POLICY_KB = [
    {"id": "KYC-1.1", "policy": "KYC Master Policy", "text": "Customer identification procedures for new account opening require government-issued photo ID."},
    {"id": "KYC-1.3", "policy": "KYC Master Policy", "text": "Aadhaar-based eKYC is accepted as valid identification for individual accounts."},
    {"id": "AML-2.1", "policy": "AML Compliance Policy", "text": "Suspicious transaction reporting must be filed within 7 days of detection to the FIU."},
    {"id": "AML-2.3", "policy": "AML Compliance Policy", "text": "Enhanced due diligence applies to politically exposed persons and high-risk customers."},
    {"id": "OPS-3.1", "policy": "General Banking Operations", "text": "All customer accounts and deposit structures must adhere to the latest RBI guidelines regarding interest rates and classification."},
    {"id": "OPS-3.2", "policy": "General Banking Operations", "text": "Banks must maintain required Cash Reserve Ratios (CRR) and Statutory Liquidity Ratios (SLR) strictly per regulatory limits."},
    {"id": "SEBI-4.1", "policy": "SEBI Disclosure Policy", "text": "Material information must be disclosed to stock exchanges within 24 hours."},
]

# Keywords that map regulatory changes to internal policies
POLICY_KEYWORDS = {
    "KYC Master Policy": ["kyc", "know your customer", "pan", "aadhaar", "identification", "identity", "ekyc", "selfie", "biometric"],
    "AML Compliance Policy": ["aml", "anti-money laundering", "suspicious", "transaction", "reporting", "fiu", "due diligence", "high risk"],
    "General Banking Operations": ["account", "customer", "deposit", "interest", "ratio", "liquidity", "reserve", "bank", "rural", "guideline", "credit"],
    "SEBI Disclosure Policy": ["sebi", "disclosure", "insider", "trading", "material information", "stock exchange", "listed"],
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
                matches.append({"policy": policy_name, "chunk": best_chunk, "score": score})
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
                    relevance_score=float(m["score"]) / 10.0  # Normalize to 0-1
                ))

    impacts.sort(key=lambda x: x.relevance_score, reverse=True)
    return impacts[:10]
