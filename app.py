import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. PAGE SETUP
st.set_page_config(page_title="TrueMetrics | Intelligence", page_icon="🎯", layout="wide")

# STYLE CONSTANTS
ACCENT_BLUE = "#3B82F6"
ACCENT_LIME = "#A3E635"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"

# 2. UI STYLING
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [data-testid="stAppViewContainer"] {{
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }}
    div[data-testid="stMetric"] {{
        background: {GLASS_BG} !important;
        backdrop-filter: blur(12px);
        border: 1px solid {GLASS_BORDER} !important;
        border-radius: 20px !important;
        padding: 20px !important;
    }}
    .glass-pane {{
        background: {GLASS_BG};
        backdrop-filter: blur(12px);
        border: 1px solid {GLASS_BORDER};
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 20px;
    }}
    .hero-text {{
        font-size: 50px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALIZATION
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- HEADER ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)

# --- APP LOGIC ---
if st.session_state.m is None:
    st.markdown("<h1 class='hero-text'>Precision Intelligence.</h1>", unsafe_allow_html=True)
    up = st.file_uploader("Upload Data", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m

    # A. DATA MAPPING PREVIEW
    with st.expander("🔍 DATA MAPPING VERIFICATION", expanded=True):
        if "mapping_preview" in m:
            st.table(pd.DataFrame(m["mapping_preview"]))
        else:
            st.warning("Mapping data not available.")

    # B. KPI GRID
    st.markdown("### Performance Matrix")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Revenue", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("Profit", f"{m['total_profit']:,.0f} SAR")
    k3.metric("Margin", f"{m['margin_pct']}%")
    k4.metric("Records", f"{m['total_units']:,}")

    # C. VISUALS & CHAT
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1.5, 1])

    with c_left:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        if m.get('trend_data'):
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.line(tdf, x='Date', y='Sales', title="Strategic Trend")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            fig.update_traces(line_color=ACCENT_BLUE, line_width=4)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{ACCENT_LIME}; font-weight:bold;'>AI CONSULTANT</p>", unsafe_allow_html=True)
        chat_box = st.container(height=300)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Analyze..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Reset System"):
        st.session_state.m = None
        st.rerun()
