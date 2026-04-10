from utils.vector_store import create_policy_collection, vector_retrieve
from rank_bm25 import BM25Okapi
import numpy as np
from typing import List

def hybrid_search(query: str, policy_chunks: List[str]) -> List[tuple]:
    if not policy_chunks:
        return []
        
    collection = create_policy_collection()
    chunk_count = collection.count()
    if chunk_count == 0:
        return []
    
    # Vector search
    k = min(100, chunk_count)
    try:
        vector_results = vector_retrieve(collection, query, k)
    except Exception:
        # Fallback if DB not ready
        return []
        
    # BM25 over the all chunks
    tokenized_corpus = [doc.split() for doc in policy_chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    query_tok = query.split()
    bm25_scores = bm25.get_scores(query_tok)
    
    results_fused = []
    
    distances = vector_results.get('distances', [[0]*k])[0]
    docs = vector_results.get('documents', [[]])[0]
    
    for i, doc in enumerate(docs):
        try:
            global_idx = policy_chunks.index(doc)
            b_score = bm25_scores[global_idx]
        except ValueError:
            b_score = 0
            
        v_score = 1.0 / (1.0 + distances[i]) # normalize
        fused = 0.7 * v_score + 0.3 * b_score
        results_fused.append((doc, fused))
        
    results_fused.sort(key=lambda x: x[1], reverse=True)
    return results_fused[:5]

