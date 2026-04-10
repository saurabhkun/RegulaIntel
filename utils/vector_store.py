import chromadb
from typing import List
import re
from pathlib import Path

_ef = None

def get_ef():
    global _ef
    if _ef is None:
        from chromadb.utils import embedding_functions
        _ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _ef

abs_path = str(Path("./chroma_db").absolute())
client = chromadb.PersistentClient(path=abs_path)

def create_policy_collection():
    return client.get_or_create_collection(
        name="internal_policies",
        embedding_function=get_ef()
    )

def index_policy(collection, chunks: List[str], metadatas: List[dict]):
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

def vector_retrieve(collection, query: str, n_results: int = 5):
    return collection.query(
        query_texts=[query],
        n_results=n_results
    )

def index_policies():
    collection = create_policy_collection()
    if collection.count() > 0:
        return collection
    with open('data/internal/kyc_policy.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    # Split into chunks by double newline or section
    chunks = [c.strip() for c in re.split(r'\n\s*\n', text) if len(c.strip()) > 10]
    metadatas = [{'source': 'kyc_policy.txt', 'type': 'policy_chunk'} for _ in chunks]
    index_policy(collection, chunks, metadatas)
    print(f"Indexed {len(chunks)} policy chunks")
    return collection
