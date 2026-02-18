import streamlit as st
import pandas as pd
import plotly.express as px
import os
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# 1. Page Config
st.set_page_config(page_title="Sahm BI | Intelligence", page_icon="📈", layout="wide")

# Sahm BI Brand Colors
SAHM_BLUE = "#1E3A8A"
SAHM_GREEN = "#10B981"

# Custom Styling for a Professional Look
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F9FAFB; }}
    .stMetric {{ background-color: white; border-radius: 10px; padding: 15px; border-left: 5px solid {SAHM_BLUE}; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
    [data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }}
    h1, h2, h3 {{ color: {SAHM_BLUE} !important; }}
    </style>
    """, unsafe_allow_html=True)

# 2. Logo & Branding Header
col_logo, col_text = st.columns([1, 5])

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        st.markdown(f"<h1 style='color: {SAHM_BLUE};'>🏹</h1>", unsafe_allow_html=True)

with col_text:
    st.title("Sahm BI — سهم للذكاء الأعمال")
    st.markdown(f"<p style='font-size:18px; color:#4B5563; font-weight: 500;'>Strategic Enterprise Analytics for Saudi SMEs</p>", unsafe_allow_html=True)

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

if st.session_state.m is None:
    st.divider()
    up = st.file_uploader("Upload Business Intelligence Data (CSV/Excel)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(g_client, raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    
    with st.sidebar:
        st.markdown(f"<h3 style='text-align: center;'>Control Panel</h3>", unsafe_allow_html=True)
        if st.button("🗑️ Reset Sahm BI", use_container_width=True):
            st.session_state.m = None
            st.session_state.chat = []
            st.rerun()
        st.divider()
        st.info("Sahm BI uses dual-engine AI to provide real-time Saudi tax and sales advice.")

    # --- KPI DASHBOARD ---
    st.subheader("🏦 Executive Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sales", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("Total Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("Units Sold", f"{m.get('total_units', 0):,}")
    k4.metric("VAT (15%)", f"{m.get('vat_due', 0):,.0f} SAR")

    st.divider()

    # --- MARGINS ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### 📉 Bottom Performers")
        for item in m.get('bot_margin_list', []): st.error(item)
    with col_b:
        st.markdown(f"### 📈 Top Performers")
        for item in m.get('top_margin_list', []): st.success(item)

    # --- TREND CHART (Color Matched) ---
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Month', 'Sales'])
        # Customizing the chart to Sahm BI colors
        fig = px.line(tdf, x='Month', y='Sales', 
                      title="📈 Sahm BI Revenue Performance", 
                      markers=True,
                      color_discrete_sequence=[SAHM_BLUE])
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
        fig.update_traces(line_width=3, marker=dict(size=8, color=SAHM_GREEN))
        st.plotly_chart(fig, use_container_width=True)

    # --- CHAT ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Ask Sahm AI Consultant"):
        st.markdown(f"<h4 style='color:{SAHM_BLUE};'>Business Advisor</h4>", unsafe_allow_html=True)
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask Sahm BI..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
