import streamlit as st
import os
import traceback
import html
import re
import pandas as pd
from dotenv import load_dotenv
from agents.workflow import graph as workflow_graph
from utils.report_generator import ReportGenerator

load_dotenv(override=True)

def clean(text: str, limit: int = 160) -> str:
    """Strip markdown syntax, escape HTML, collapse whitespace for safe card injection."""
    if not text:
        return ""
    # Strip markdown headers, bold, italic, links, list bullets
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # # headers
    text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)         # **bold** / *italic*
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)        # [link](url)
    text = re.sub(r'https?://\S+', '', text)                     # bare URLs
    text = re.sub(r'[\r\n\t]+', ' ', text)                       # newlines → space
    text = re.sub(r'\s{2,}', ' ', text).strip()                  # collapse spaces
    text = html.escape(text)                                      # escape remaining HTML
    if len(text) > limit:
        text = text[:limit] + '…'
    return text

st.set_page_config(
    page_title="RegulaIntel | Compliance Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

*, html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp { background-color: #F9FAFB; }
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display:none; }

/* Column panels - target deepest container */
[data-testid="stVerticalBlock"] {
    background: transparent;
}

/* Alerts */
.stSuccess { background:#ECFDF5 !important; border-left:3px solid #059669 !important; color:#065F46 !important; }
.stInfo    { background:#EFF6FF !important; border-left:3px solid #0052CC !important; color:#1E40AF !important; }
.stWarning { background:#FFFBEB !important; border-left:3px solid #D97706 !important; }
.stError   { background:#FEF2F2 !important; border-left:3px solid #DC2626 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #E2E8F0; background:transparent; }
.stTabs [data-baseweb="tab"] { font-size:.85rem; font-weight:500; color:#64748B; padding:8px 16px; }
.stTabs [aria-selected="true"] { color:#0052CC !important; border-bottom:2px solid #0052CC !important; }

/* Expander */
.streamlit-expanderHeader { font-weight:600; font-size:.88rem; color:#0F172A; }


/* Metric */
[data-testid="stMetric"] { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; }
[data-testid="stMetricValue"] { font-size:1.6rem !important; font-weight:700 !important; color:#0F172A !important; }
[data-testid="stMetricLabel"] { font-size:.75rem !important; color:#64748B !important; }

/* Progress bar */
.stProgress > div > div { background-color: #0052CC !important; }

/* Cards */
.intel-card {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    background: #FFFFFF;
}
.card-title  { font-size:.9rem;  font-weight:600; color:#0F172A; margin-bottom:3px; }
.card-meta   { font-size:.75rem; color:#64748B;   margin-bottom:6px; }
.card-body   { font-size:.82rem; color:#475569; }
.badge       { padding:2px 9px; border-radius:20px; font-size:.72rem; font-weight:600; }
.badge-critical { background:#FEE2E2; color:#DC2626; }
.badge-moderate { background:#FEF3C7; color:#D97706; }
.badge-low      { background:#DCFCE7; color:#059669; }
.live-dot { display:inline-block; width:7px; height:7px; background:#059669; border-radius:50%; margin-right:4px; animation:pulse 1.5s infinite; }
.off-dot  { display:inline-block; width:7px; height:7px; background:#CBD5E1; border-radius:50%; margin-right:4px; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }

.policy-chip {
    border: 1px solid #E2E8F0; border-radius:7px;
    padding:8px 12px; margin-bottom:6px;
    background:#F8FAFC; font-size:.82rem; color:#0F172A;
}
.section-label {
    font-size:.68rem; font-weight:700; color:#64748B;
    text-transform:uppercase; letter-spacing:.06em;
    margin: 14px 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for k, v in [("results", None), ("selected_idx", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Top Nav ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
     padding:12px 4px 18px 4px;border-bottom:1px solid #E2E8F0;margin-bottom:16px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:1.15rem;font-weight:700;color:#0F172A;">⚖️ RegulaIntel</span>
    <span style="background:#0052CC;color:#fff;font-size:.65rem;padding:2px 8px;
          border-radius:20px;font-weight:600;">AI-POWERED</span>
  </div>
  <div style="font-size:.8rem;color:#64748B;">Autonomous Regulatory Compliance · Indian Financial Sector</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# THREE-COLUMN LAYOUT
# ═══════════════════════════════════════════════════════════
left, center, right = st.columns([1, 2.2, 1.8], gap="medium")

# ──────────────────────────────────────────────────────────
# LEFT — Sources & Upload
# ──────────────────────────────────────────────────────────
with left:
    st.markdown('<div class="section-label">📡 Intelligence Sources</div>', unsafe_allow_html=True)
    for src, full, live in [
        ("RBI",   "Reserve Bank of India",          True),
        ("SEBI",  "Securities & Exchange Board",     True),
        ("MCA",   "Ministry of Corporate Affairs",   False),
        ("IRDAI", "Insurance Regulatory Auth.",       False),
    ]:
        dot = '<span class="live-dot"></span>' if live else '<span class="off-dot"></span>'
        status = '<span style="color:#059669;font-size:.72rem;font-weight:600">LIVE</span>' if live else '<span style="color:#94A3B8;font-size:.72rem">OFFLINE</span>'
        st.markdown(f"""
        <div style="padding:9px 10px;border-radius:7px;margin-bottom:4px;border:1px solid #F1F5F9;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-weight:600;font-size:.88rem;color:#0F172A">{src}</div>
              <div style="font-size:.73rem;color:#64748B">{full}</div>
            </div>
            <div>{dot}{status}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:16px">🔍 Analyze Circulars</div>', unsafe_allow_html=True)
    old_pdf = st.file_uploader("Old Circular (baseline)", type="pdf", key="old")
    new_pdf = st.file_uploader("New Circular (latest)", type="pdf", key="new")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Run Analysis", type="primary", use_container_width=True, disabled=not (old_pdf and new_pdf)):
        old_path, new_path = "temp_old.pdf", "temp_new.pdf"
        with open(old_path, "wb") as f: f.write(old_pdf.getvalue())
        with open(new_path, "wb") as f: f.write(new_pdf.getvalue())
        try:
            with st.spinner("Agents running…"):
                result = workflow_graph.invoke({"old_pdf": old_path, "new_pdf": new_path})
            st.session_state.results = result
            st.session_state.selected_idx = 0
            st.rerun()
        except Exception as e:
            st.error(str(e))
        finally:
            for f in [old_path, new_path]:
                if os.path.exists(f): os.unlink(f)

    if st.button("🎯 Load Demo", use_container_width=True):
        with st.spinner("Running demo…"):
            try:
                result = workflow_graph.invoke({
                    "old_pdf": "data/circulars/old/demo_old.pdf",
                    "new_pdf": "data/circulars/new/demo_new.pdf"
                })
                st.session_state.results = result
                st.session_state.selected_idx = 0
                st.rerun()
            except Exception as e:
                st.error(str(e))

    if st.session_state.results:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Clear Results", use_container_width=True):
            st.session_state.results = None
            st.cache_resource.clear()
            st.rerun()

# ──────────────────────────────────────────────────────────
# CENTER — Intelligence Feed
# ──────────────────────────────────────────────────────────
with center:
    st.markdown('<div class="section-label">📋 Intelligence Feed</div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;color:#94A3B8;">
          <div style="font-size:2.5rem;margin-bottom:12px;">📂</div>
          <div style="font-weight:600;color:#64748B;font-size:.95rem;margin-bottom:6px;">No analysis yet</div>
          <div style="font-size:.84rem">Upload two PDF circulars or click <b>Load Demo</b></div>
        </div>""", unsafe_allow_html=True)
    else:
        changes    = st.session_state.results.get('changes', [])
        impacts    = st.session_state.results.get('impacts', [])
        amendments = st.session_state.results.get('amendments', [])

        n_crit = sum(1 for c in changes if getattr(c,'severity','LOW')=='CRITICAL')
        n_mod  = sum(1 for c in changes if getattr(c,'severity','LOW')=='MODERATE')
        n_low  = len(changes) - n_crit - n_mod

        # Summary strip
        st.markdown(f"""
        <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center;">
          <span class="badge badge-critical">{n_crit} Critical</span>
          <span class="badge badge-moderate">{n_mod} Moderate</span>
          <span class="badge badge-low">{n_low} Low</span>
          <span style="margin-left:auto;font-size:.78rem;color:#64748B;">
            {len(changes)} changes · {len(impacts)} policies · {len(amendments)} amendments
          </span>
        </div>""", unsafe_allow_html=True)

        # Alert for critical
        if n_crit > 0:
            try:
                from utils.alerter import send_slack_alert
                send_slack_alert("CRITICAL", f"{n_crit} critical regulatory changes detected.")
                st.toast("🔔 Autonomous webhook dispatched!", icon="🚨")
            except Exception:
                pass

        if not changes:
            st.info("No significant changes detected between the two circulars.")
        else:
            for idx, c in enumerate(changes):
                sev    = getattr(c, 'severity', 'LOW')
                sec_id = getattr(c, 'section_id', f'Section {idx+1}')
                page   = getattr(c, 'page_number', '?')
                score  = getattr(c, 'similarity_score', 0)
                new_t  = getattr(c, 'new_text', '')
                conf   = getattr(c, 'confidence', '')

                selected_style = "border-color:#0052CC;background:#EFF6FF;" if st.session_state.selected_idx == idx else ""
                st.markdown(f"""
                <div class="intel-card" style="{selected_style}">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                      <div class="card-title">{html.escape(sec_id)}</div>
                      <div class="card-meta">Page {page} &nbsp;&middot;&nbsp; {html.escape(conf)} &nbsp;&middot;&nbsp; {score:.1%} similar</div>
                    </div>
                    <span class="badge badge-{sev.lower()}">{sev}</span>
                  </div>
                  <div class="card-body">{clean(new_t, 160)}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("Select →", key=f"sel_{idx}"):
                    st.session_state.selected_idx = idx
                    st.rerun()

# ──────────────────────────────────────────────────────────
# RIGHT — Action & Impact
# ──────────────────────────────────────────────────────────
with right:
    st.markdown('<div class="section-label">⚡ Action & Impact</div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;color:#94A3B8;">
          <div style="font-size:2rem;margin-bottom:10px;">👆</div>
          <div style="font-size:.84rem">Select a change to see its<br>policy impact & amendments.</div>
        </div>""", unsafe_allow_html=True)
    else:
        changes    = st.session_state.results.get('changes', [])
        impacts    = st.session_state.results.get('impacts', [])
        amendments = st.session_state.results.get('amendments', [])
        idx        = st.session_state.selected_idx

        if changes and idx < len(changes):
            c      = changes[idx]
            sec_id = getattr(c, 'section_id', 'Unknown')
            sev    = getattr(c, 'severity', 'LOW')
            score  = getattr(c, 'similarity_score', 0)
            old_t  = getattr(c, 'old_text', '')
            new_t  = getattr(c, 'new_text', '')

            sev_color = {"CRITICAL":"#DC2626","MODERATE":"#D97706","LOW":"#059669"}.get(sev,"#64748B")
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin-bottom:12px;">
              <div style="font-weight:700;font-size:.9rem;color:#0F172A;margin-bottom:4px;">{sec_id}</div>
              <span class="badge badge-{sev.lower()}">{sev}</span>
              <span style="margin-left:8px;font-size:.78rem;color:#64748B">Similarity: {score:.1%}</span>
            </div>""", unsafe_allow_html=True)

            with st.expander("📄 Text Comparison", expanded=False):
                st.markdown("**Before:**")
                st.code(clean(old_t, 400) or "(empty)", language=None)
                st.markdown("**After:**")
                st.code(clean(new_t, 400) or "(empty)", language=None)

            # Impacted policies
            st.markdown('<div class="section-label">🏛️ Impacted Policies</div>', unsafe_allow_html=True)
            s_impacts = [i for i in impacts if i.section_id == sec_id] or impacts[:3]
            if s_impacts:
                for imp in s_impacts[:3]:
                    st.markdown(f"""
                    <div class="policy-chip">
                      <div style="display:flex;align-items:flex-start;gap:8px;">
                        <div style="width:8px;height:8px;border-radius:50%;background:#DC2626;margin-top:4px;flex-shrink:0"></div>
                        <div>
                          <div style="font-weight:600;font-size:.82rem">{imp.policy_name}</div>
                          <div style="color:#64748B;font-size:.75rem;margin-top:2px">{clean(imp.matched_text, 90)}</div>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("No matching internal policies found.")

            # Amendments
            st.markdown('<div class="section-label">✏️ Proposed Amendment</div>', unsafe_allow_html=True)
            s_amends = [a for a in amendments if a.section_id == sec_id] or amendments[:1]
            if s_amends:
                a = s_amends[0]
                st.markdown(f"**{a.policy_name}**")
                st.text_area("Proposed Text", value=a.proposed_text,
                             key=f"ta_{idx}_{a.section_id}", height=110, label_visibility="collapsed")
                st.caption(f"💡 {a.justification[:130]}")
            else:
                st.caption("No amendments drafted. Check your GROQ_API_KEY.")

            # Export
            st.markdown('<div class="section-label">📥 Export Report</div>', unsafe_allow_html=True)
            if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
                try:
                    rg = ReportGenerator()
                    rg.generate_report(changes, amendments, "compliance_report.pdf")
                    with open("compliance_report.pdf", "rb") as f:
                        st.download_button("⬇️ Download PDF", data=f,
                            file_name="RegulaIntel_Report.pdf",
                            mime="application/pdf", use_container_width=True)
                    st.success("Report generated!")
                except Exception as e:
                    st.error(f"Report error: {e}")

        # Full summary table below
        if changes:
            st.markdown("---")
            st.markdown('<div class="section-label">📊 All Changes</div>', unsafe_allow_html=True)
            df = pd.DataFrame([{
                "Page": getattr(c,'page_number','?'),
                "Section": getattr(c,'section_id','?'),
                "Severity": getattr(c,'severity','LOW'),
                "Score": f"{getattr(c,'similarity_score',0):.0%}",
            } for c in changes])
            st.dataframe(df, use_container_width=True, hide_index=True, height=180)
