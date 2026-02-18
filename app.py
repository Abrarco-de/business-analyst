import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# Page Config
st.set_page_config(page_title="Visionary SME AI", layout="wide", page_icon="📈")

# 1. SESSION STATE
if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

# API Init
g_key, m_key = st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY")
g_client, m_client = configure_dual_engines(g_key, m_key)

st.title("📊 Enterprise BI Dashboard")

# 2. FILE UPLOADER
if st.session_state.m is None:
    st.info("👋 Welcome! Please upload your Sales/Finance data (CSV or Excel).")
    up = st.file_uploader("Upload Data", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        with st.spinner("Analyzing Data..."):
            metrics, _ = process_business_data(g_client, raw)
            if "error" in metrics:
                st.error(metrics["error"])
            else:
                st.session_state.m = metrics
                st.rerun()
else:
    if st.sidebar.button("🗑️ Reset All Data"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

# 3. DASHBOARD UI
if st.session_state.m:
    m = st.session_state.m
    meta = m['meta']
    
    # Row 1: KPI Metrics
    st.subheader("💰 Financial Status")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", f"{m['revenue']:,} SAR")
    
    # Label profit clearly if estimated
    p_label = "Total Profit" if meta['real_profit'] else "Estimated Profit (20%)"
    k2.metric(p_label, f"{m['profit']:,} SAR")
    
    k3.metric("Gross Margin", f"{m['margin_pct']}%")
    k4.metric("VAT (15%)", f"{m['vat']:,} SAR")

    st.divider()

    # Row 2: Sorted Tables (The "Least Margin" Request)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📉 Weakest Margins (Sorted)")
        for item in m['bot_margin_items']:
            st.error(item)
            
    with col_b:
        st.markdown("### 📈 Strongest Margins (Sorted)")
        for item in m['top_margin_items']:
            st.success(item)

    # Row 3: Trend Chart (Conditional)
    if m['trend_data']:
        st.divider()
        st.subheader("📅 Revenue Trend Over Time")
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Date', 'Revenue'])
        fig = px.line(tdf, x='Date', y='Revenue', markers=True, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Note: No valid date column found to generate trend chart.")

    # 4. CHAT POPOVER
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Chat with AI"):
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
            
        if p := st.chat_input("Ask about your performance..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
