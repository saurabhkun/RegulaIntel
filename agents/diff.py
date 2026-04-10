from langchain_core.tools import tool
from utils.models import Change
from typing import List
import numpy as np

# Lazy-loaded model — avoids HTTP client closed error at import time
_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def jaccard_similarity(s1: str, s2: str) -> float:
    set1 = set(s1.lower().split())
    set2 = set(s2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

@tool
def compute_diff(old_sections: list, new_sections: list) -> List[Change]:
    """Compute semantic diff between old/new sections using Hybrid (Cosine + Lexical)."""
    model = get_model()
    changes = []

    for old in old_sections:
        old_text = old.get('text', '')
        if not old_text:
            continue
        old_emb = model.encode(old_text)

        best_match = None
        best_score = -1

        for new_s in new_sections:
            new_text = new_s.get('text', '')
            if not new_text:
                continue
            new_emb = model.encode(new_text)

            cos_sim = float(np.dot(old_emb, new_emb) / (np.linalg.norm(old_emb) * np.linalg.norm(new_emb) + 1e-9))
            jac_sim = jaccard_similarity(old_text, new_text)

            final_score = 0.7 * cos_sim + 0.3 * jac_sim
            if final_score > best_score:
                best_score = final_score
                best_match = new_s

        if not best_match:
            continue

        # Classify change severity
        if best_score > 0.95:
            conf = 'NO_CHANGE'
            sev  = 'LOW'
        elif best_score >= 0.85:
            conf = 'MINOR_EDIT'
            sev  = 'MODERATE'
        else:
            conf = 'SIGNIFICANT_CHANGE'
            sev  = 'CRITICAL'

        if conf != 'NO_CHANGE':
            changes.append(Change(
                section_id=old.get('id', 'Unknown'),
                old_text=old_text,
                new_text=best_match.get('text', ''),
                similarity_score=best_score,
                confidence=conf,
                page_number=best_match.get('page', 1),
                severity=sev
            ))

    return changes
