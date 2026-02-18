import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. SETUP
st.set_page_config(page_title="TrueMetrics | Intelligence", page_icon="🎯", layout="wide")

ACCENT_BLUE = "#3B82F6"
ACCENT_LIME = "#A3E635"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.1)"

# 2. THEME & BRANDING
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
        font-size: 56px; font-weight: 800; letter-spacing: -2px;
        background: linear-gradient(to right, #ffffff, #94a3b8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }}
    .tagline {{
        color: {ACCENT_BLUE};
        font-weight: 700;
        letter-spacing: 3px;
        font-size: 14px;
        text-transform: uppercase;
        margin-bottom: 40px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. ENGINE INIT
g_client, m_client = configure_dual_engines(
    st.secrets.get("GROQ_API_KEY"), 
    st.secrets.get("MISTRAL_API_KEY")
)

if "m" not in st.session_state: 
    st.session_state.m = None
if "chat" not in st.session_state: 
    st.session_state.chat = []

# --- HEADER ---
col_head, _ = st.columns([1, 4])
with col_head:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.markdown(f"<h1 style='color:{ACCENT_LIME}; margin:0;'>🎯</h1>", unsafe_allow_html=True)

# --- APP FLOW ---
if st.session_state.m is None:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-text'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Precision in every data point</p>", unsafe_allow_html=True)
    
    up = st.file_uploader("Initialize Intelligence System (CSV/XLSX)", type=["csv", "xlsx"])
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
            st.error(f"File Error: {e}")
else:
    m = st.session_state.m

    # Verification Table
    with st.expander("🔍 AI DATA MAPPING PREVIEW", expanded=False):
        if "mapping_preview" in m:
            st.table(pd.DataFrame(m["mapping_preview"]))
    
    # KPIs
    st.markdown("### Performance Matrix")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("REVENUE", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("PROFIT", f"{m['total_profit']:,.0f} SAR")
    k3.metric("MARGIN", f"{m['margin_pct']}%")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")
    k5.metric("units sold", f"{m['total_units']:,}")

    # Margin Alerts Row
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"<p style='color:#ef4444; font-weight:bold;'>📉 LOW MARGIN ALERTS</p>", unsafe_allow_html=True)
        for i in m.get('bot_margin_list', []):
            st.markdown(f"<div style='background:rgba(239, 68, 68, 0.1); border-left:4px solid #ef4444; padding:10px; border-radius:5px; margin-bottom:5px; font-size:13px;'>{i}</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"<p style='color:{ACCENT_LIME}; font-weight:bold;'>📈 PEAK MARGIN ITEMS</p>", unsafe_allow_html=True)
        for i in m.get('top_margin_list', []):
            st.markdown(f"<div style='background:rgba(163, 230, 53, 0.1); border-left:4px solid {ACCENT_LIME}; padding:10px; border-radius:5px; margin-bottom:5px; font-size:13px;'>{i}</div>", unsafe_allow_html=True)

    # C. VISUALS & CHAT
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1.5, 1])

    with c_left:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        if m.get('trend_data'):
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.line(tdf, x='Date', y='Sales', title="Strategic Revenue Growth")
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            fig.update_traces(line_color=ACCENT_BLUE, line_width=4, fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)')
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='glass-pane'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{ACCENT_LIME}; font-weight:bold;'>TRUEMETRICS AI CONSULTANT</p>", unsafe_allow_html=True)
        chat_box = st.container(height=300)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): 
                    st.write(msg["content"])
        
        if p := st.chat_input("Analyze metrics..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Reset System"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

