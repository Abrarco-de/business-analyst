import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

# 1. SETUP
st.set_page_config(page_title="TrueMetrics | Intelligence", page_icon="🎯", layout="wide")
BLUE, LIME, DARK = "#3B82F6", "#A3E635", "#020617"

# 2. THEME (Aura Design)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    .stApp {{
        background: radial-gradient(circle at 0% 0%, rgba(59,130,246,0.12) 0%, transparent 25%),
                    radial-gradient(circle at 100% 100%, rgba(163,230,53,0.08) 0%, transparent 25%), {DARK};
        font-family: 'Plus Jakarta Sans', sans-serif; color: #f8fafc;
    }}
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important; padding: 20px !important;
    }}
    .glass-card {{
        background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px; padding: 25px; margin-bottom: 20px;
    }}
    .hero-title {{ font-size: 64px; font-weight: 800; letter-spacing: -3px; color: #fff; margin-bottom: 0px; }}
    .tagline {{ color: {BLUE}; font-weight: 700; letter-spacing: 5px; font-size: 12px; text-transform: uppercase; margin-bottom: 40px; }}
    .dist-bar-bg {{ background: rgba(255,255,255,0.05); border-radius: 10px; height: 8px; width: 100%; margin-top: 4px; }}
    .dist-bar-fill {{ background: {BLUE}; height: 8px; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# 3. INITIALIZATION
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- FLOW ---
if st.session_state.m is None:
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Precision in every data point</p>", unsafe_allow_html=True)
    up = st.file_uploader("Upload Business Data", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m

    # Verification Table
    with st.expander("🔍 DATA MAPPING PREVIEW", expanded=False):
        st.table(pd.DataFrame(m["mapping_preview"]))

    # 1. KPI MATRIX
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("REVENUE", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("PROFIT", f"{m['total_profit']:,.0f} SAR")
    k3.metric("MARGIN", f"{m['margin_pct']}%")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")
    k5.metric("RECORDS", f"{m['units']:,}")

    # 2. GRAPHS & INSIGHTS GRID
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Trend Graph
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Strategic Growth Trend")
        if m['trend_data']:
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.area(tdf, x='Date', y='Sales')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350, margin=dict(l=0,r=0,t=10,b=0))
            fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=4)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Bottom Alerts
        a1, a2 = st.columns(2)
        with a1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#ef4444; font-weight:800; font-size:12px;'>LOW MARGIN RISKS</p>", unsafe_allow_html=True)
            for i in m['bot_margins']: st.caption(f"⚠️ {i}")
            st.markdown("</div>", unsafe_allow_html=True)
        with a2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#A3E635; font-weight:800; font-size:12px;'>PEAK PERFORMANCE</p>", unsafe_allow_html=True)
            for i in m['top_margins']: st.caption(f"💎 {i}")
            st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        # Market Distribution Bars
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📍 Market Share (City)")
        for city, val in m['city_dist'].items():
            pct = (val / m['total_revenue']) * 100
            st.markdown(f"<p style='margin:0; font-size:13px;'>{city} <span style='float:right; color:{BLUE}'>{pct:.1f}%</span></p>", unsafe_allow_html=True)
            st.markdown(f"<div class='dist-bar-bg'><div class='dist-bar-fill' style='width:{pct}%'></div></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # AI Consultant
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"#### 💬 AI Agent")
        chat_box = st.container(height=240)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Analyze..."):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": get_ai_response(m_client, m, p)})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("System Reset"):
        st.session_state.m = None
        st.rerun()
