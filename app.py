import streamlit as st
import pandas as pd
import plotly.express as px
import os
import Truemetrics as tm

# 1. SETUP
st.set_page_config(page_title="TrueMetrics | Ultra BI", page_icon="🎯", layout="wide")
BLUE, LIME, DARK = "#3B82F6", "#A3E635", "#020617"

# 2. UI STYLING
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
    .tagline {{ color: {BLUE}; font-weight: 700; letter-spacing: 5px; font-size: 11px; text-transform: uppercase; margin-bottom: 40px; }}
    .dist-bar-bg {{ background: rgba(255,255,255,0.05); border-radius: 10px; height: 8px; width: 100%; margin-top: 4px; }}
    .dist-bar-fill {{ background: {BLUE}; height: 8px; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# 3. CORE LOGIC
g_client, m_client = tm.configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# --- APP FLOW ---
if st.session_state.m is None:
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title'>TrueMetrics</h1>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Precision in every data point</p>", unsafe_allow_html=True)
    up = st.file_uploader("Upload CSV/XLSX to Begin", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = tm.process_business_data(raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m

    # Verification Expander
    with st.expander("🔍 AI LOGIC PREVIEW (Mapping)", expanded=False):
        st.table(pd.DataFrame(m["mapping_preview"]))

    # 1. TOP KPI ROW
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("REVENUE", f"{m['total_revenue']:,.0f} SAR")
    k2.metric("PROFIT", f"{m['total_profit']:,.0f} SAR")
    k3.metric("MARGIN", f"{m['margin_pct']}%")
    k4.metric("VAT (15%)", f"{m['vat_due']:,.0f} SAR")
    k5.metric("RECORDS", f"{m['units']:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. DATA GRID
    c_main, c_side = st.columns([2, 1])

    with c_main:
        # Growth Trend
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Strategic Growth Trajectory")
        if m['trend_data']:
            tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Sales'])
            fig = px.area(tdf, x='Date', y='Sales')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', height=350, margin=dict(l=0,r=0,t=10,b=0))
            fig.update_traces(line_color=BLUE, fillcolor='rgba(59, 130, 246, 0.1)', line_width=4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No time-series data found to plot trend.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Margin Alerts
        ma1, ma2 = st.columns(2)
        with ma1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#ef4444; font-weight:800; font-size:12px;'>LOW MARGIN RISKS</p>", unsafe_allow_html=True)
            for i in m['bot_margins']: st.caption(f"⚠️ {i}")
            st.markdown("</div>", unsafe_allow_html=True)
        with ma2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:{LIME}; font-weight:800; font-size:12px;'>PEAK PERFORMANCE</p>", unsafe_allow_html=True)
            for i in m['top_margins']: st.caption(f"💎 {i}")
            st.markdown("</div>", unsafe_allow_html=True)

    with c_side:
        # Market Share (City/Store)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("#### 📍 Market Share")
        if m['city_dist']:
            for loc, val in m['city_dist'].items():
                pct = (val / m['total_revenue']) * 100
                st.markdown(f"<p style='margin:0; font-size:13px;'>{loc} <span style='float:right; color:{BLUE}'>{pct:.1f}%</span></p>", unsafe_allow_html=True)
                st.markdown(f"<div class='dist-bar-bg'><div class='dist-bar-fill' style='width:{pct}%'></div></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        else:
            st.caption("No regional distribution data found.")
        st.markdown("</div>", unsafe_allow_html=True)

        # AI Chat
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"#### 💬 AI Consultant")
        chat_box = st.container(height=240)
        with chat_box:
            for msg in st.session_state.chat:
                with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Analyze results..."):
            st.session_state.chat.append({"role": "user", "content": p})
            st.session_state.chat.append({"role": "assistant", "content": tm.get_ai_response(m_client, m, p)})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.sidebar.button("Clear Dashboard"):
        st.session_state.m = None
        st.rerun()
