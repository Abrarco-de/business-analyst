import streamlit as st
import pandas as pd
import plotly.express as px
import os
from Truemetrics import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="TrueMetrics | Ultra BI", page_icon="🎯", layout="wide")

# CUSTOM UI CONSTANTS
BLUE = "#3B82F6"
LIME = "#A3E635"
DARK = "#020617"

# ADVANCED CSS (AURA DESIGN)
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    .stApp {{
        background: radial-gradient(circle at 0% 0%, rgba(59, 130, 246, 0.15) 0%, transparent 25%),
                    radial-gradient(circle at 100% 100%, rgba(163, 230, 53, 0.1) 0%, transparent 25%),
                    {DARK};
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f8fafc;
    }}

    /* Glowing Metrics */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 25px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    }}
    
    div[data-testid="stMetric"]:hover {{
        border-color: {BLUE} !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
    }}

    .glass-card {{
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 24px;
        margin-bottom: 20px;
    }}

    .hero-title {{
        font-size: 72px; font-weight: 800; letter-spacing: -3px;
        background: linear-gradient(135deg, #fff 0%, #64748b 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1; margin-bottom: 10px;
    }}

    .tagline {{
        color: {BLUE}; font-weight: 700; letter-spacing: 5px; font-size: 12px;
        text-transform: uppercase; margin-bottom: 50px;
    }}

    /* Custom Distribution Bars */
    .dist-bar-bg {{ background: rgba(255,255,255,0.05); border-radius: 10px; height: 8px; width: 100%; margin-top: 4px; }}
    .dist-bar-fill {{ background: {BLUE}; height: 8px; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# ENGINES
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- DASHBOARD LOGIC ---
if st.session_state.m is None:
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Precision in every data point</p>", unsafe_allow_html=True)
    
    up = st.file_uploader("", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m

    # 1. TOP STATS
    st.markdown("### 💠 Performance Overview")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("REVENUE", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("NET PROFIT", f"{m['total_profit']:,.0f} SAR")
    k3.metric("MARGIN", f"{m['margin_pct']}%")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")
    k5.metric("RECORDS", f"{m['units']:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. MAIN GRID
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Revenue Trajectory")
        if m['trend_data']:
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.area(tdf, x='Date', y='Sales')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350, margin=dict(l=0,r=0,t=20,b=0))
            fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=4)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Alerts Row
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

    with c2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📍 Top Locations")
        for city, val in m['city_dist'].items():
            pct = (val / m['total_revenue']) * 100
            st.markdown(f"<p style='margin:0; font-size:13px;'>{city} <span style='float:right; color:{BLUE}'>{pct:.1f}%</span></p>", unsafe_allow_html=True)
            st.markdown(f"<div class='dist-bar-bg'><div class='dist-bar-fill' style='width:{pct}%'></div></div>", unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card' style='height:300px'>", unsafe_allow_html=True)
        st.markdown(f"#### 💬 AI Consultant")
        chat_box = st.container(height=180)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Speak to Engine..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Reset Session"):
        st.session_state.m = None
        st.rerun()
