import streamlit as st
import requests
import os
import re

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Procurement Copilot",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Theme Custom CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── Google Font ─── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&display=swap');

/* ─── Global ─── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #1e293b;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
}

.stApp {
    background: #f8fafc;
}

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
    color: #475569;
    font-size: 0.95rem;
}

/* ─── Hero Banner ─── */
.hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    color: white;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    position: relative;
    overflow: hidden;
}
.hero-banner::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.4) 0%, rgba(0,0,0,0) 70%);
    border-radius: 50%;
}
.hero-banner h2 {
    color: white !important;
    margin: 0 0 0.75rem 0;
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.hero-banner p {
    color: #cbd5e1;
    margin: 0;
    font-size: 1.05rem;
    line-height: 1.6;
    max-width: 800px;
}

/* ─── Chat Messages ─── */
[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}

[data-testid="stChatMessage"]:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
}

/* ─── Chat Input ─── */
[data-testid="stChatInput"] {
    padding-bottom: 2rem;
}
[data-testid="stChatInput"] textarea {
    border-radius: 20px !important;
    border: 2px solid #cbd5e1 !important;
    background: #ffffff !important;
    font-size: 1rem;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
}

/* ─── Sidebar Capability Cards ─── */
.cap-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.cap-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08);
    border-color: #cbd5e1;
}
.cap-card .cap-icon {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
}
.cap-card .cap-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 1rem;
    margin-bottom: 0.25rem;
    font-family: 'Outfit', sans-serif;
}
.cap-card .cap-desc {
    color: #64748b;
    font-size: 0.85rem;
    line-height: 1.5;
}

/* ─── Metric Cards ─── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: left;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: #6366f1;
}
.metric-card .metric-val {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    font-family: 'Outfit', sans-serif;
}
.metric-card .metric-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.5rem;
}

/* ─── Footer ─── */
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 0.85rem;
    margin-top: 4rem;
    padding: 1.5rem 0;
    border-top: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏢 Procurement Copilot")
    st.caption("Enterprise AI Agent Platform")

    if st.button("🗑️ New Chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # Example Questions
    st.markdown("### 💬 Try Asking")
    questions = [
        "How much did we spend on TechCorp Inc.?",
        "What are the SLA terms for CloudServe?",
        "List all active contracts and their values.",
        "Total procurement spend across all vendors?",
        "Which vendors are non-compliant?",
    ]
    for q in questions:
        if st.button(q, use_container_width=True):
            st.session_state.queued_prompt = q
            st.rerun()

    st.markdown("---")

    # Agent Architecture
    st.markdown("### 🤖 Agent Fleet")
    st.markdown("""
    <div class="cap-card">
        <div class="cap-icon">🧠</div>
        <div class="cap-title">Supervisor</div>
        <div class="cap-desc">Orchestrator that routes questions and handles multi-step reasoning.</div>
    </div>
    <div class="cap-card">
        <div class="cap-icon">📊</div>
        <div class="cap-title">Data Analyst</div>
        <div class="cap-desc">Queries financial tables via SQL.</div>
    </div>
    <div class="cap-card">
        <div class="cap-icon">📑</div>
        <div class="cap-title">Policy Researcher</div>
        <div class="cap-desc">Searches ChromaDB for SLAs & compliance docs.</div>
    </div>
    <div class="cap-card">
        <div class="cap-icon">⚙️</div>
        <div class="cap-title">Platform Ops</div>
        <div class="cap-desc">Manages GitHub, secrets, and Cloud infrastructure via MCP.</div>
    </div>
    """, unsafe_allow_html=True)

# ── Main Content ─────────────────────────────────────────────────────────────

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <h2>Enterprise Procurement Copilot</h2>
    <p>An intelligent multi-agent platform designed to autonomously resolve complex procurement inquiries. Powered by Google Vertex AI, LangGraph, and specialized sub-agents.</p>
</div>
""", unsafe_allow_html=True)

# Quick Metrics
st.markdown("""
<div class="metric-row">
    <div class="metric-card" style="border-left-color: #3b82f6;">
        <div class="metric-val">4</div>
        <div class="metric-label">Vendors Tracked</div>
    </div>
    <div class="metric-card" style="border-left-color: #10b981;">
        <div class="metric-val">$265K</div>
        <div class="metric-label">Total Contract Value</div>
    </div>
    <div class="metric-card" style="border-left-color: #8b5cf6;">
        <div class="metric-val">5</div>
        <div class="metric-label">Purchase Orders</div>
    </div>
    <div class="metric-card" style="border-left-color: #f59e0b;">
        <div class="metric-val">3</div>
        <div class="metric-label">AI Sub-Agents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Chat Interface ───────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "trace" in message and message["trace"]:
            with st.expander("🕵️ Observability Trace", expanded=False):
                st.markdown(f"**Agent Flow:** `{message['trace']}`")
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about vendors, contracts, spend, or policies..."):
    st.session_state.queued_prompt = prompt

if "queued_prompt" in st.session_state:
    prompt = st.session_state.queued_prompt
    del st.session_state.queued_prompt

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        obs_trace = ["Supervisor"]
        final_text = ""
        
        # UI Elements
        trace_expander = st.expander("🕵️ Observability Trace", expanded=True)
        with trace_expander:
            trace_placeholder = st.empty()
            trace_placeholder.markdown(f"**Agent Flow:** `{' ➔ '.join(obs_trace)}`")
            
        message_placeholder = st.empty()

        try:
            backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
            # In local dev or cloud run, we hit the streaming endpoint
            headers = {"Authorization": "Bearer mock-secret-token"}
            payload = {"message": prompt, "session_id": "123"}

            with requests.post(
                f"{backend_url}/chat/stream",
                json=payload,
                headers=headers,
                stream=True,
                timeout=120,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data: "):
                            data = decoded[6:]
                            if data == "[DONE]":
                                break
                            
                            # Parse SSE format: [AgentName] Content
                            # For example: [Supervisor] Routing to DataAnalyst...
                            match = re.match(r"^\[(.*?)\] (.*)", data)
                            if match:
                                agent = match.group(1)
                                content = match.group(2)
                                
                                if agent == "Supervisor" and "Routing to" in content:
                                    target = content.replace("Routing to ", "").replace("...", "").strip()
                                    if target != "FINISH":
                                        obs_trace.append(target)
                                        trace_placeholder.markdown(f"**Agent Flow:** `{' ➔ '.join(obs_trace)}`")
                                    else:
                                        obs_trace.append("FINISH")
                                        trace_placeholder.markdown(f"**Agent Flow:** `{' ➔ '.join(obs_trace)}` (Completed)")
                                else:
                                    # This is actual conversational output
                                    # Avoid appending repeated tool invocation strings to final text if we only want the clean answer
                                    final_text += content + "\n"
                            else:
                                # Raw fallback data
                                if "Routing to" not in data:
                                    final_text += data + "\n"
                            
                            message_placeholder.markdown(final_text + " ▌")
                            
            message_placeholder.markdown(final_text)
            
        except requests.exceptions.RequestException as e:
            final_text = (
                f"⚠️ **Connection Error**\n\n"
                f"Unable to reach the backend at `{os.environ.get('BACKEND_URL', 'http://localhost:8000')}`.\n\n"
                f"Details: `{e}`"
            )
            message_placeholder.markdown(final_text)
            trace_placeholder.markdown(f"**Agent Flow:** `{' ➔ '.join(obs_trace)}` (Failed)")

    st.session_state.messages.append({
        "role": "assistant", 
        "content": final_text,
        "trace": " ➔ ".join(obs_trace)
    })

# Footer
st.markdown(
    '<div class="footer">Powered by Google Vertex AI · LangGraph · ChromaDB · Google Cloud Run</div>',
    unsafe_allow_html=True,
)
