import pymupdf4llm
from typing import List, Dict
from utils.models import StructuredDocument
import re

def process_pdf(pdf_path: str) -> List[Dict]:
    """Standalone PDF processor for ingest agent."""
    import pymupdf4llm
    md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True, write_images=False)
    
    sections = []
    
    for page_dict in md_pages:
        page_num = page_dict.get('metadata', {}).get('page', 1)
        text = page_dict.get('text', '')
        if text.strip():
            sections.append({
                'id': f"page_{page_num}",
                'text': text.strip(),
                'page': page_num
            })
    return sections

def extract_pdf_sections(pdf_path: str) -> StructuredDocument:
    """Extract markdown with page chunks using regex matching for sections."""
    # Use pymupdf4llm to get page-wise markdown
    md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True, write_images=False)
    
    sections = []
    
    for page_dict in md_pages:
        page_num = page_dict.get('metadata', {}).get('page', 1)
        text = page_dict.get('text', '')
        
        # Split text into sections using regex r'(Section\s+\d+\.\d+)'
        parts = re.split(r'(Section\s+\d+\.\d+)', text)
        
        # If no sections block found, just chunk the whole page
        if len(parts) == 1:
            if text.strip():
                sections.append({
                    'id': f"Page_{page_num}",
                    'text': text.strip(),
                    'page': page_num
                })
            continue
            
        # First part might be pre-section text
        if parts[0].strip():
            sections.append({
                'id': f"Page_{page_num}_intro",
                'text': parts[0].strip(),
                'page': page_num
            })
            
        # Reconstruct sections
        for i in range(1, len(parts), 2):
            sec_id = parts[i].strip()
            sec_content = parts[i+1].strip() if i+1 < len(parts) else ""
            if sec_content:
                sections.append({
                    'id': sec_id,
                    'text': f"{sec_id}\n{sec_content}",
                    'page': page_num
                })
                
    return StructuredDocument(sections=sections, metadata={'path': pdf_path})
