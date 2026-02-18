import streamlit as st
import pandas as pd
import plotly.express as px
import os
# Importing from your renamed logic file
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="TrueMetrics | Precision Intelligence", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# BRAND COLORS
ACCENT_BLUE = "#3B82F6"
ACCENT_LIME = "#A3E635"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"

# 2. PREMIUM TPCAP CSS STYLING
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {{
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617);
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
    }}

    /* Glassmorphic Metric Cards */
    div[data-testid="stMetric"] {{
        background: {GLASS_BG} !important;
        backdrop-filter: blur(16px);
        border: 1px solid {GLASS_BORDER} !important;
        border-radius: 24px !important;
        padding: 25px !important;
        transition: transform 0.3s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-5px);
        border-color: {ACCENT_BLUE} !important;
    }}

    /* Custom Glass Panes for Charts/Chat */
    .glass-pane {{
        background: {GLASS_BG};
        backdrop-filter: blur(12px);
        border: 1px solid {GLASS_BORDER};
        border-radius: 24px;
        padding: 20px;
        margin-bottom: 20px;
    }}

    /* Typography */
    .hero-text {{
        font-size: 56px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }}
    
    /* Clean Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: rgba(15, 23, 42, 0.9) !important;
    }}

    /* Mapping Table Customization */
    [data-testid="stExpander"] {{
        background: {GLASS_BG} !important;
        border: 1px solid {GLASS_BORDER} !important;
        border-radius: 15px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALIZE ENGINES & SESSION
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- HEADER / LOGO ---
col_l, col_r = st.columns([1, 4])
with col_l:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=160)
    else:
        st.markdown(f"<h1 style='color:{ACCENT_LIME}; margin:0;'>🎯</h1>", unsafe_allow_html=True)

# --- APP STATES ---

# STATE A: FILE UPLOAD (WELCOME SCREEN)
if st.session_state.m is None:
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-text'>Precision intelligence<br>starts here.</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#94a3b8; font-size:18px; margin-bottom:40px;'>Upload your business records to begin the TrueMetrics analysis.</p>", unsafe_allow_html=True)
    
    up = st.file_uploader("", type=["csv", "xlsx"])
    if up:
        try:
            raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            m, _ = process_business_data(raw)
            if "error" in m:
                st.error(m["error"])
            else:
                st.session_state.m = m
                st.rerun()
        except Exception as e:
            st.error(f"Upload failed: {e}")

# STATE B: ACTIVE DASHBOARD
else:
    m = st.session_state.m
    
    # 1. MAPPING VERIFICATION (Transparent & Interactive)
    with st.expander("🔍 AI DATA MAPPING PREVIEW", expanded=False):
        st.markdown("<p style='font-size:14px; color:#94a3b8;'>Check how our engine interpreted your file headers:</p>", unsafe_allow_html=True)
        if "mapping_preview" in m:
            pdf = pd.DataFrame(m["mapping_preview"])
            st.dataframe(pdf, use_container_width=True, hide_index=True)
        st.info("Verified: Logic applied across all records.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. KPI MATRIX (The Grid)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("REVENUE", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("NET PROFIT", f"{m['total_profit']:,.0f} SAR")
    k3.metric("MARGIN", f"{m['margin_pct']}%")
    k4.metric("VOL.", f"{m['total_units']:,}")

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # 3. INTERACTIVE VISUALS & CHAT
    col_viz, col_chat = st.columns([1.6, 1])

    with col_viz:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:600; letter-spacing:1px; margin-bottom:20px;'>STRATEGIC REVENUE TREND</p>", unsafe_allow_html=True)
        if m.get('trend_data'):
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.line(tdf, x='Date', y='Sales', template="plotly_dark")
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=0, r=0, t=10, b=0),
                height=380
            )
            fig.update_traces(line_color=ACCENT_BLUE, line_width=4, fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chat:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:600; color:{ACCENT_LIME};'>TRUEMETRICS AI CONSULTANT</p>", unsafe_allow_html=True)
        
        # Chat Display
        chat_box = st.container(height=320)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Input
        if p := st.chat_input("Analyze performance..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. SIDEBAR ACTIONS
    with st.sidebar:
        st.markdown(f"<h2 style='color:{ACCENT_BLUE}'>TrueMetrics</h2>", unsafe_allow_html=True)
        st.caption("v2.0 Precision Engine")
        st.divider()
        if st.button("RESET SYSTEM", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()
