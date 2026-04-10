import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

def test_setup():
    print("🔍 Sunhack_Hackathon Setup Test")
    
    # 1. PDF files
    old_pdf = Path("data/circulars/old/demo_old.pdf")
    new_pdf = Path("data/circulars/new/demo_new.pdf")
    print(f"📄 Old PDF: {'✅' if old_pdf.exists() else '❌'}")
    print(f"📄 New PDF: {'✅' if new_pdf.exists() else '❌'}")
    
    # 2. Groq API key
    groq_key = os.getenv("GROQ_API_KEY")
    print(f"🔑 Groq API: {'✅' if groq_key else '❌'}")
    
    # 3. ChromaDB
    try:
        import traceback
        abs_path = str(Path("./chroma_db").absolute())
        client = chromadb.PersistentClient(path=abs_path)
        print("🗄️  ChromaDB: ✅")
    except Exception as e:
        print(f"🗄️  ChromaDB: ❌ {e}")
        traceback.print_exc()
    
    # 4. Embedding model
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("🤖 Embedding model: ✅")
    except Exception as e:
        print(f"🤖 Embedding model: ❌ {e}")
    
    print("\nSetup complete! Run `streamlit run app.py`")

if __name__ == "__main__":
    test_setup()
