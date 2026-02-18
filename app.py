import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

# Initialize Session State
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# API Connections
g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

st.title("📊 SME Business Intelligence")

# 1. FILE LOADER
if st.session_state.m is None:
    up = st.file_uploader("Upload your Business Data (CSV/Excel)", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(g_client, raw)
        if "error" in m:
            st.error(f"Error: {m['error']}")
        else:
            st.session_state.m = m
            st.rerun()
else:
    # 2. DATA ACCESS (Safe mode)
    m = st.session_state.m
    meta = m.get('meta', {})
    
    if st.sidebar.button("🗑️ Clear & Upload New"):
        st.session_state.m = None
        st.rerun()

    # 3. KPI DASHBOARD
    st.subheader("🏦 Financial Overview")
    k1, k2, k3 = st.columns(3)
    
    # Using .get() ensures no KeyErrors ever happen
    k1.metric("Total Revenue", f"{m.get('total_revenue', 0):,.0f} SAR")
    
    prof_label = f"Profit ({meta.get('profit_method', 'Est.')})"
    k2.metric(prof_label, f"{m.get('total_profit', 0):,.0f} SAR")
    
    k3.metric("Gross Margin", f"{m.get('margin_pct', 0)}%")

    st.divider()

    # 4. MARGIN ANALYSIS
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📉 Least Margin Items")
        for item in m.get('bot_margin_list', []):
            st.error(item)
    with col_b:
        st.subheader("📈 Top Margin Items")
        for item in m.get('top_margin_list', []):
            st.success(item)

    # 5. TREND GRAPH
    if m.get('trend_data'):
        st.divider()
        st.subheader("📈 Revenue Trend")
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Revenue'])
        st.plotly_chart(px.line(tdf, x='Date', y='Revenue', markers=True))

    # 6. FLOATING AI CHAT
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Chat with Strategist"):
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask about your data..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
