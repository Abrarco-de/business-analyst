import streamlit as st
import pandas as pd
import plotly.express as px
import Truemetrics as tm

# 1. UI CONFIGURATION
st.set_page_config(page_title="TrueMetrics | Universal", page_icon="🌐", layout="wide")
BLUE, DARK, PANEL = "#3B82F6", "#020617", "rgba(255, 255, 255, 0.03)"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Inter:wght@400;500&display=swap');
    .stApp {{ background: {DARK}; color: #f8fafc; font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Outfit', sans-serif !important; margin: 0; }}
    div[data-testid="stMetric"] {{
        background: {PANEL} !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 20px !important; padding: 20px !important;
    }}
    .glass-card {{
        background: {PANEL}; border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
    }}
    .status-bar {{ padding: 8px 15px; border-radius: 50px; background: rgba(59,130,246,0.1); color: {BLUE}; font-weight: 600; font-size: 11px; display: inline-block; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# 2. SAFE API INITIALIZATION
# This prevents the crash if secrets are missing
GROQ_K = st.secrets.get("GROQ_API_KEY", None)
MIST_K = st.secrets.get("MISTRAL_API_KEY", None)
g_client, m_client = tm.configure_dual_engines(GROQ_K, MIST_K)

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- [ HEADER SECTION ] ---
st.markdown("<h1 style='font-size:54px;'>TrueMetrics</h1>", unsafe_allow_html=True)
st.markdown("<div class='status-bar'>UNIVERSAL BUSINESS ENGINE ACTIVE</div>", unsafe_allow_html=True)

# --- [ DATA UPLOAD / RESET ] ---
if st.session_state.m is None:
    up = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m_data, _ = tm.process_business_data(raw)
        if "error" in m_data: st.error(m_data["error"])
        else:
            st.session_state.m = m_data
            st.rerun()
else:
    m = st.session_state.m
    if st.sidebar.button("🗑️ Reset & New File"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    # --- [ KPI STRIP ] ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Revenue", f"{m.get('total_revenue', 0):,.2f}")
    k2.metric("📈 Est. Profit", f"{m.get('total_profit', 0):,.2f}")
    k3.metric("🎯 Margin %", f"{m.get('margin_pct', 0)}%")
    k4.metric("🔮 Forecast", f"{m.get('forecast', 0):,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- [ CONFIDENCE & MAPPING ] ---
    with st.expander(f"🔍 System Confidence: {m.get('confidence', 0)}%", expanded=False):
        st.table(pd.DataFrame(m.get('mapping_preview', [])))

    # --- [ INSIGHTS COLUMNS ] ---
    c_top, c_risk = st.columns(2)
    with c_top:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>💎 Top Performers ({m.get('loc_header', 'Segment')})</h4>", unsafe_allow_html=True)
        for i in m.get('top_margins', []): st.success(i)
        st.markdown("</div>", unsafe_allow_html=True)
    with c_risk:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>⚠️ Margin Risks</h4>", unsafe_allow_html=True)
        for i in m.get('bot_margins', []): st.error(i)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ TREND CHART ] ---
    if m.get('trend_data'):
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4>📊 Revenue Timeline</h4>", unsafe_allow_html=True)
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
        fig = px.area(tdf, x='Date', y='Sales')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=300)
        fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [ FLOATING CHAT POPOVER ] ---
    with st.popover("💬 Ask AI Analyst"):
        if not m_client: 
            st.error("Mistral API Key missing in secrets.toml")
        else:
            chat_box = st.container(height=300)
            for msg in st.session_state.chat:
                with chat_box.chat_message(msg["role"]): st.write(msg["content"])
            
            if p := st.chat_input("Ask: 'What is the highest sale?'"):
                st.session_state.chat.append({"role": "user", "content": p})
                st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
                st.rerun()
