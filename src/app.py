import json
import uuid
from datetime import datetime

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Secure RAG Brain — Enterprise Admin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional blueprint aesthetic
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #EEF2F1;
        --bg-secondary: #FFFFFF;
        --accent-primary: #145DA0;
        --accent-hover: #0B3D6E;
        --accent-light: #E8F1F8;
        --quarantine-bg: #FDF2F2;
        --quarantine-border: #EC4899;
        --approved-bg: #F0FDF4;
        --approved-border: #22C55E;
        --text-primary: #1A1F24;
        --text-secondary: #4A5568;
        --border-color: #D1D9E0;
    }
    
    .stApp {
        background-color: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    
    .main-caption {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .status-connected {
        background: var(--approved-bg);
        color: var(--approved-border);
        border: 1px solid var(--approved-border);
    }
    
    .status-active {
        background: var(--accent-light);
        color: var(--accent-primary);
        border: 1px solid var(--accent-primary);
    }
    
    .status-warning {
        background: #FEF3C7;
        color: #D97706;
        border: 1px solid #FBBF24;
    }
    
    .quarantine-box {
        background: var(--quarantine-bg);
        border-left: 4px solid var(--quarantine-border);
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .approved-box {
        background: var(--approved-bg);
        border-left: 4px solid var(--approved-border);
        border-radius: 4px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .stButton > button {
        background-color: var(--accent-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        padding: 0.625rem 1.25rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: background-color 0.15s ease !important;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-hover) !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.875rem !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px var(--accent-light) !important;
    }
    
    .metric-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--accent-primary);
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }
    
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .code-block {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        background: #1A1F24;
        color: #E2E8F0;
        padding: 1rem;
        border-radius: 6px;
        overflow-x: auto;
    }
    
    .sidebar-content {
        padding: 0.5rem 0;
    }
    
    .tenant-badge {
        display: inline-block;
        background: var(--accent-light);
        color: var(--accent-primary);
        padding: 0.25rem 0.5rem;
        border-radius: 3px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "documents" not in st.session_state:
    st.session_state.documents = []
if "stats" not in st.session_state:
    st.session_state.stats = {"total": 0, "approved": 0, "quarantined": 0, "pending": 0}

# Header
st.markdown('<div class="main-header">🛡️ Secure RAG Brain</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-caption">Asynchronous Serverless Ingress Gate & Vector Space Isolation Engine</div>',
    unsafe_allow_html=True,
)

# Sidebar - System Status
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚙️ Core Infrastructure</div>', unsafe_allow_html=True)

    # Status indicators
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(
            '<div class="status-indicator status-connected">●</div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown("**Database** — Connected (Supabase Postgres)")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div class="status-indicator status-active">●</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**Vector Space** — HNSW Graph Index Active")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div class="status-indicator status-warning">●</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("**RLS Boundary** — Strict Tenant Mode Enforced")

    st.markdown("---")

    # Tenant selector
    st.markdown(
        '<div class="section-header">🔐 Active Tenant Context</div>', unsafe_allow_html=True
    )
    tenant_id = st.text_input(
        "JWT-Bound User ID",
        value="tenant-usr-489x-wells",
        help="This would be extracted from the validated JWT in production",
    )
    st.markdown(f'<div class="tenant-badge">{tenant_id}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Statistics
    st.markdown('<div class="section-header">📊 Pipeline Metrics</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats["total"]}</div>
                <div class="metric-label">Total Documents</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats["approved"]}</div>
                <div class="metric-label">Approved</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats["quarantined"]}</div>
                <div class="metric-label">Quarantined</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.stats["pending"]}</div>
                <div class="metric-label">Pending Review</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

# Main content area - Two columns
col1, col2 = st.columns([1, 1.2])

# LEFT COLUMN: Data Ingest Triage
with col1:
    st.markdown('<div class="section-header">📥 Data Ingest Triage</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="status-card">', unsafe_allow_html=True)

        doc_title = st.text_input(
            "Document Reference Title",
            placeholder="e.g., Q3 Financial Review",
            help="Unique identifier for this document in the tenant namespace",
        )

        uploaded_text = st.text_area(
            "Raw Document Content",
            height=280,
            placeholder="Paste or type document content here...\n\nPII patterns (SSN, AWS keys, credit cards, emails, phones, API keys) will be automatically detected and flagged.",
            help="Content is scanned client-side for demo; production uses async Lambda triage",
        )

        # Scan preview (client-side simulation)
        if uploaded_text:
            import re

            pii_patterns = {
                "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
                "AWS Access Key": r"\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b",
                "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
                "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "Phone (US)": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "API Key": r"\b(sk-|pk-|rk-)[A-Za-z0-9]{32,}\b",
            }

            detected = []
            for pii_type, pattern in pii_patterns.items():
                matches = re.findall(pattern, uploaded_text)
                if matches:
                    detected.append((pii_type, len(matches)))

            if detected:
                st.markdown("**⚠️ Pre-scan Detection:**")
                for pii_type, count in detected:
                    st.markdown(
                        f'<div class="quarantine-box"><strong>{pii_type}</strong>: {count} match(es) found</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="approved-box">✅ No PII patterns detected in pre-scan</div>',
                    unsafe_allow_html=True,
                )

        submit_col, clear_col = st.columns([2, 1])
        with submit_col:
            submit_btn = st.button(
                "Submit to Secure Ingress Pipeline",
                type="primary",
                use_container_width=True,
                disabled=not (doc_title and uploaded_text),
            )
        with clear_col:
            if st.button("Clear", use_container_width=True):
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Process submission
    if submit_btn and doc_title and uploaded_text:
        with st.spinner("Executing serverless compliance scan..."):
            # Simulate async Lambda processing
            import time

            time.sleep(1.5)

            # Run PII detection
            import re

            pii_patterns = {
                "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
                "AWS Access Key": r"\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b",
                "Credit Card": r"\b(?:\d[ -]*?){13,16}\b",
                "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                "Phone (US)": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                "API Key": r"\b(sk-|pk-|rk-)[A-Za-z0-9]{32,}\b",
            }

            detected_types = []
            matches = {}
            for pii_type, pattern in pii_patterns.items():
                found = re.findall(pattern, uploaded_text)
                if found:
                    detected_types.append(pii_type)
                    matches[pii_type] = found[:3]

            has_pii = len(detected_types) > 0
            status = "quarantined" if has_pii else "approved"

            # Create document record
            doc_id = str(uuid.uuid4())[:8]
            document = {
                "id": doc_id,
                "title": doc_title,
                "content": uploaded_text[:200] + ("..." if len(uploaded_text) > 200 else ""),
                "status": status,
                "pii_types": detected_types,
                "matches": matches,
                "tenant": tenant_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "full_content": uploaded_text,
            }

            st.session_state.documents.insert(0, document)

            # Update stats
            st.session_state.stats["total"] += 1
            if status == "approved":
                st.session_state.stats["approved"] += 1
            else:
                st.session_state.stats["quarantined"] += 1

            if has_pii:
                st.error(f"🔴 **QUARANTINED** — {len(detected_types)} PII type(s) detected")
                for pii_type in detected_types:
                    st.markdown(
                        f'<div class="quarantine-box"><strong>{pii_type}</strong>: {matches[pii_type]}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("🟢 **APPROVED** — Document cleared for vector ingestion")

            st.info(f"Document ID: `{doc_id}` | Status: `{status}` | Tenant: `{tenant_id}`")

# RIGHT COLUMN: Document Registry & Vector Space
with col2:
    st.markdown(
        '<div class="section-header">📋 Document Registry & Vector Space</div>',
        unsafe_allow_html=True,
    )

    # Filter tabs
    tab1, tab2, tab3 = st.tabs(["🟢 Approved", "🔴 Quarantined", "⏳ All Documents"])

    with tab1:
        approved_docs = [d for d in st.session_state.documents if d["status"] == "approved"]
        if approved_docs:
            for doc in approved_docs:
                st.markdown(
                    f"""
                    <div class="approved-box">
                        <strong>{doc["title"]}</strong> <span style="color: var(--text-secondary); font-size: 0.75rem;">({doc["id"]})</span><br>
                        <span style="color: var(--text-secondary); font-size: 0.8rem;">{doc["timestamp"]} | {doc["tenant"]}</span><br>
                        <span style="font-size: 0.75rem;">{doc["content"][:100]}...</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="approved-box">No approved documents yet. Submit clean content to populate vector space.</div>',
                unsafe_allow_html=True,
            )

    with tab2:
        quarantined_docs = [d for d in st.session_state.documents if d["status"] == "quarantined"]
        if quarantined_docs:
            for doc in quarantined_docs:
                pii_badges = "".join(
                    [
                        f'<span style="background: var(--quarantine-bg); color: var(--quarantine-border); padding: 0.125rem 0.375rem; border-radius: 3px; font-size: 0.65rem; margin-right: 0.25rem;">{t}</span>'
                        for t in doc["pii_types"]
                    ]
                )
                st.markdown(
                    f"""
                    <div class="quarantine-box">
                        <strong>{doc["title"]}</strong> <span style="color: var(--text-secondary); font-size: 0.75rem;">({doc["id"]})</span><br>
                        <span style="color: var(--text-secondary); font-size: 0.8rem;">{doc["timestamp"]} | {doc["tenant"]}</span><br>
                        <div style="margin-top: 0.5rem;">{pii_badges}</div>
                        <details style="margin-top: 0.5rem;">
                            <summary style="cursor: pointer; font-size: 0.75rem; color: var(--quarantine-border);">View detected matches</summary>
                            <pre style="margin-top: 0.5rem; font-size: 0.7rem; background: #FFF5F5; padding: 0.5rem; border-radius: 3px;">{json.dumps(doc["matches"], indent=2)}</pre>
                        </details>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="quarantine-box">No quarantined documents. PII detection is working.</div>',
                unsafe_allow_html=True,
            )

    with tab3:
        if st.session_state.documents:
            for doc in st.session_state.documents:
                status_badge = "🟢" if doc["status"] == "approved" else "🔴"
                st.markdown(
                    f"""
                    <div class="status-card" style="margin-bottom: 0.5rem;">
                        {status_badge} <strong>{doc["title"]}</strong> <span style="color: var(--text-secondary); font-size: 0.75rem;">({doc["id"]})</span><br>
                        <span style="font-size: 0.75rem; color: var(--text-secondary);">{doc["timestamp"]} | {doc["tenant"]} | {doc["status"].upper()}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="status-card" style="text-align: center; color: var(--text-secondary);">No documents submitted yet. Use the ingress panel to begin.</div>',
                unsafe_allow_html=True,
            )

# Footer - Architecture Reference
st.markdown("---")
with st.expander("🏗️ Architecture Reference — Secure RAG Brain Data Flow"):
    st.markdown("""
    ```
    ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
    │   Client    │────▶│  API Gateway     │────▶│  S3 (Raw Land)  │────▶│  Lambda Triage   │
    │  (Streamlit)│     │  /ingest         │     │  Bucket         │     │  (PII Scanner)   │
    └─────────────┘     └──────────────────┘     └─────────────────┘     └────────┬─────────┘
                                                                                   │
                                                                                   ▼
    ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
    │   Vector    │◀────│  Supabase        │◀────│  Classification │◀────│  Status Update   │
    │  Search UI  │     │  (pgvector +     │     │  Engine         │     │  (RLS Bypass)    │
    │             │     │   HNSW Index)    │     │                 │     │                  │
    └─────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
    ```
    
    **Key Security Properties:**
    - **Zero-Trust Tenancy**: PostgreSQL RLS enforces `user_id = auth.uid()` at database layer
    - **Async PII Gate**: Lambda scans *before* vector embedding — contaminated text never reaches LLM context
    - **Cost Efficiency**: Regex + NER locally ≈ $0.00/GB vs. $0.50+/GB for managed PII scanners
    - **Audit Trail**: Every document carries `classification_status`, `detected_pii_types`, `pii_matches`
    """)

# Footer
st.markdown(
    """
    <div style="text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.75rem;">
        Secure RAG Brain v1.0 | Built by Raina Wells | 
        <a href="https://github.com/rwells489/secure-rag-brain" style="color: var(--accent-primary);">GitHub</a> • 
        <a href="https://linkedin.com/in/rainawells" style="color: var(--accent-primary);">LinkedIn</a>
    </div>
""",
    unsafe_allow_html=True,
)
