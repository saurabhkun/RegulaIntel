from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from .ingest import ingest_pdf
from .diff import compute_diff
from .impact import assess_impact
from .drafter import draft_amendments
import os

llm = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview", temperature=0) if os.getenv("GROQ_API_KEY") else None

tools = [ingest_pdf, compute_diff, assess_impact, draft_amendments] if llm else []

supervisor = create_react_agent(llm, tools) if llm else None

