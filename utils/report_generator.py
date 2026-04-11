from fpdf import FPDF
from datetime import datetime
from typing import List
import re
import os

def _s(text, limit=500):
    """Safe text: break long words, truncate, encode to latin-1, strip markdown."""
    if not text:
        return ""
    text = str(text)
    # Strip PyMuPDF4LLM picture placeholders
    text = re.sub(r'==>\s*picture\s*\[.*?\]\s*intentionally\s*omitted\s*<==', '', text)
    text = re.sub(r'[#*`~_]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = []
    for w in text.split():
        while len(w) > 55:
            words.append(w[:55])
            w = w[55:]
        words.append(w)
    text = " ".join(words)[:limit]
    # Drop unsupported characters (like Hindi strings) instead of mapping them to '?'
    return text.encode("latin-1", "ignore").decode("latin-1")


class ReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)
        self.pdf.set_margins(20, 15, 20)

    def _heading(self, text, size=14):
        self.pdf.set_font("Helvetica", "B", size)
        self.pdf.set_text_color(30, 64, 175)   # Blue heading
        self.pdf.cell(0, 9, _s(text, 120), ln=True)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.set_font("Helvetica", "", 10)

    def _subheading(self, text):
        self.pdf.set_font("Helvetica", "B", 10)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, _s(text, 100), ln=True)
        self.pdf.set_text_color(0, 0, 0)

    def _body(self, text):
        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.multi_cell(0, 6, _s(text))

    def _divider(self):
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(20, self.pdf.get_y(), 190, self.pdf.get_y())
        self.pdf.ln(3)

    def generate_report(self, changes: list, amendments: list, output_path="compliance_report.pdf"):
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            
            now = datetime.now().strftime("%d %B %Y, %I:%M %p")

            # ── Cover Page ────────────────────────────────────────────────────────
            self.pdf.add_page()
            self.pdf.set_fill_color(30, 64, 175)
            self.pdf.rect(0, 0, 210, 60, "F")

            self.pdf.set_y(18)
            self.pdf.set_font("Helvetica", "B", 22)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.cell(0, 10, "RegulaIntel Compliance Report", ln=True, align="C")
            self.pdf.set_font("Helvetica", "", 11)
            self.pdf.cell(0, 8, f"Generated: {now}", ln=True, align="C")
            self.pdf.set_text_color(0, 0, 0)

            self.pdf.set_y(70)

            # ── Executive Summary ─────────────────────────────────────────────────
            self._heading("Executive Summary", 14)
            self._divider()

            n_critical = sum(1 for c in changes if getattr(c, 'severity', 'LOW') == 'CRITICAL')
            n_moderate = sum(1 for c in changes if getattr(c, 'severity', 'LOW') == 'MODERATE')
            n_low = len(changes) - n_critical - n_moderate

            summary = (
                f"This report presents the findings of an automated regulatory compliance analysis "
                f"conducted using the RegulaIntel multi-agent AI system. A total of {len(changes)} "
                f"regulatory changes were detected, of which {n_critical} are classified as CRITICAL "
                f"(requiring immediate attention), {n_moderate} as MODERATE, and {n_low} as LOW risk. "
                f"Based on these changes, {len(amendments)} internal policy amendments have been drafted "
                f"by the AI drafting agent to bring internal policies in alignment with the new regulations."
            )
            self._body(summary)
            self.pdf.ln(4)

            # Risk Table
            self.pdf.set_font("Helvetica", "B", 10)
            self.pdf.set_fill_color(240, 240, 240)
            self.pdf.cell(63, 7, "Risk Level", border=1, fill=True, align="C")
            self.pdf.cell(63, 7, "Count", border=1, fill=True, align="C")
            self.pdf.cell(64, 7, "Action Required", border=1, fill=True, align="C")
            self.pdf.ln()
            rows = [
                ("CRITICAL", str(n_critical), "Immediate policy update required"),
                ("MODERATE", str(n_moderate), "Review within 7 days"),
                ("LOW",      str(n_low),      "Monitor for future updates"),
            ]
            self.pdf.set_font("Helvetica", "", 10)
            for r in rows:
                self.pdf.cell(63, 6, r[0], border=1, align="C")
                self.pdf.cell(63, 6, r[1], border=1, align="C")
                self.pdf.cell(64, 6, r[2], border=1, align="C")
                self.pdf.ln()
            self.pdf.ln(6)

            # ── Detected Changes ──────────────────────────────────────────────────
            self._heading("Section 1: Detected Regulatory Changes")
            self._divider()

            if not changes:
                self._body("No significant changes were detected between the two circulars.")
            else:
                for i, c in enumerate(changes):
                    sec_id = getattr(c, 'section_id', f'Section {i+1}')
                    page   = getattr(c, 'page_number', '?')
                    sev    = getattr(c, 'severity', 'LOW')
                    conf   = getattr(c, 'confidence', 'N/A')
                    score  = getattr(c, 'similarity_score', 0)
                    old_t  = getattr(c, 'old_text', '')
                    new_t  = getattr(c, 'new_text', '')

                    self._subheading(f"Change {i+1}: {sec_id}  |  Page {page}  |  {sev}")
                    self.pdf.set_font("Helvetica", "", 9)
                    self.pdf.set_text_color(100, 100, 100)
                    self.pdf.cell(0, 5, f"Confidence: {conf}   |   Similarity Score: {score:.1%}", ln=True)
                    self.pdf.set_text_color(0, 0, 0)
                    self.pdf.ln(1)

                    self.pdf.set_font("Helvetica", "I", 9)
                    self.pdf.cell(0, 5, "Old Text:", ln=True)
                    self.pdf.set_font("Helvetica", "", 9)
                    self.pdf.set_text_color(120, 60, 60)
                    self.pdf.multi_cell(0, 5, _s(old_t, 300))
                    self.pdf.set_text_color(0, 0, 0)

                    self.pdf.set_font("Helvetica", "I", 9)
                    self.pdf.cell(0, 5, "New Text:", ln=True)
                    self.pdf.set_font("Helvetica", "", 9)
                    self.pdf.set_text_color(40, 100, 60)
                    self.pdf.multi_cell(0, 5, _s(new_t, 300))
                    self.pdf.set_text_color(0, 0, 0)
                    self.pdf.ln(4)
                    self._divider()

            # ── Proposed Amendments ───────────────────────────────────────────────
            self._heading("Section 2: Proposed Internal Policy Amendments")
            self._divider()

            if not amendments:
                self._body("No amendments were drafted. Ensure the GROQ_API_KEY is set for LLM-powered drafting.")
            else:
                for i, a in enumerate(amendments):
                    p_name = getattr(a, 'policy_name', '')
                    s_id   = getattr(a, 'section_id', '')
                    curr   = getattr(a, 'current_text', '')
                    prop   = getattr(a, 'proposed_text', '')
                    just   = getattr(a, 'justification', '')
                    cite   = getattr(a, 'source_citation', '')
                    dept   = getattr(a, 'department', 'Unknown')
                    effort = getattr(a, 'implementation_effort', 'MEDIUM')
                    systems = getattr(a, 'affected_systems', [])
                    testing = getattr(a, 'testing_required', True)

                    self._subheading(f"Amendment {i+1}: {p_name} — Section {s_id}")

                    # Implementation Metadata
                    self.pdf.set_font("Helvetica", "", 9)
                    self.pdf.set_text_color(60, 80, 150)
                    self.pdf.cell(0, 5, f"Department: {dept}  |  Implementation: {effort}  |  Testing: {'Yes' if testing else 'No'}", ln=True)
                    if systems:
                        self.pdf.cell(0, 5, f"Affected Systems: {', '.join(systems)}", ln=True)
                    self.pdf.set_text_color(0, 0, 0)
                    self.pdf.ln(2)

                    if curr:
                        self.pdf.set_font("Helvetica", "I", 9)
                        self.pdf.cell(0, 5, "Current Policy Text:", ln=True)
                        self.pdf.set_font("Helvetica", "", 9)
                        self.pdf.set_text_color(120, 60, 60)
                        self.pdf.multi_cell(0, 5, _s(curr, 300))
                        self.pdf.set_text_color(0, 0, 0)

                    self.pdf.set_font("Helvetica", "I", 9)
                    self.pdf.cell(0, 5, "Proposed Amendment:", ln=True)
                    self.pdf.set_font("Helvetica", "", 9)
                    self.pdf.set_text_color(40, 100, 60)
                    self.pdf.multi_cell(0, 5, _s(prop, 400))
                    self.pdf.set_text_color(0, 0, 0)

                    self.pdf.set_font("Helvetica", "I", 9)
                    self.pdf.cell(0, 5, f"Justification: {_s(just, 300)}", ln=True)
                    if cite:
                        self.pdf.cell(0, 5, f"Source: {_s(cite, 200)}", ln=True)
                    self.pdf.ln(4)
                    self._divider()

            # ── Impact Mapping Summary ────────────────────────────────────────────
            self._heading("Section 3: Impact Mapping & Execution Summary")
            self._divider()
            
            # Department impact summary
            departments = set()
            systems_set = set()
            for a in amendments:
                dept = getattr(a, 'department', 'Unknown')
                departments.add(dept)
                for sys in getattr(a, 'affected_systems', []):
                    systems_set.add(sys)
            
            summary_text = (
                f"This compliance update affects {len(departments)} departments and {len(systems_set)} systems. "
                f"{len([a for a in amendments if getattr(a, 'testing_required', True)])} amendments require QA testing. "
                f"Estimated implementation time: {len(amendments) * 5} minutes for automated execution."
            )
            self._body(summary_text)
            self.pdf.ln(2)
            
            if departments:
                self.pdf.set_font("Helvetica", "B", 10)
                self.pdf.cell(0, 6, "Departments Affected:", ln=True)
                self.pdf.set_font("Helvetica", "", 9)
                self.pdf.multi_cell(0, 5, ", ".join(sorted(departments)))
                self.pdf.ln(2)
            
            if systems_set:
                self.pdf.set_font("Helvetica", "B", 10)
                self.pdf.cell(0, 6, "Systems Requiring Updates:", ln=True)
                self.pdf.set_font("Helvetica", "", 9)
                for sys in sorted(systems_set):
                    self.pdf.cell(10, 5, "-", ln=False)
                    self.pdf.cell(0, 5, sys, ln=True)
                self.pdf.ln(2)

            # ── Footer ────────────────────────────────────────────────────────────
            self.pdf.set_y(-20)
            self.pdf.set_font("Helvetica", "I", 8)
            self.pdf.set_text_color(150, 150, 150)
            self.pdf.cell(0, 5, f"RegulaIntel AI Compliance System  |  {now}  |  Confidential", align="C")

            # Output PDF to file
            self.pdf.output(output_path)
            
            # Verify file was created successfully
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"PDF file was not created at {output_path}")
                
            # Check file size (should not be empty)
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise ValueError(f"Generated PDF is empty (0 bytes)")
                
            print(f"✅ Report generated successfully: {output_path} ({file_size} bytes)")
            
        except Exception as e:
            print(f"❌ Error generating report: {str(e)}")
            raise
