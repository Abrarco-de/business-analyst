import streamlit as st
import pandas as pd
import plotly.express as px
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

if "m" not in st.session_state: st.session_state.m = None
if "chat" not in st.session_state: st.session_state.chat = []

g_client, m_client = configure_dual_engines(st.secrets.get("GROQ_API_KEY"), st.secrets.get("MISTRAL_API_KEY"))

st.title("📊 SME Business Intelligence")

if st.session_state.m is None:
    up = st.file_uploader("Upload Supermart Data", type=["csv", "xlsx"])
    if up:
        raw = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
        m, _ = process_business_data(g_client, raw)
        if "error" in m: st.error(m["error"])
        else:
            st.session_state.m = m
            st.rerun()
else:
    m = st.session_state.m
    if st.sidebar.button("🗑️ Reset All"):
        st.session_state.m = None
        st.session_state.chat = []
        st.rerun()

    # --- KPI DASHBOARD ---
    st.subheader("🏦 Financials")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Sales", f"{m.get('total_revenue', 0):,.0f} SAR")
    k2.metric("Total Profit", f"{m.get('total_profit', 0):,.0f} SAR")
    k3.metric("Units/Transactions", f"{m.get('total_units', 0):,}")
    k4.metric("VAT (15%)", f"{m.get('vat_due', 0):,.0f} SAR")

    st.divider()

    # --- MARGIN TABLES ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("📉 Least Margin Items")
        for item in m.get('bot_margin_list', []): st.error(item)
    with col_b:
        st.subheader("📈 Top Margin Items")
        for item in m.get('top_margin_list', []): st.success(item)

    # --- TREND CHART ---
    if m.get('trend_data'):
        st.divider()
        tdf = pd.DataFrame(m['trend_data'].items(), columns=['Month', 'Sales'])
        st.plotly_chart(px.line(tdf, x='Month', y='Sales', markers=True))

    # --- CHAT POPOVER ---
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Ask the Data Expert"):
        st.write("I can now answer questions like: 'How many Masalas were sold?' or 'What are the sales in Ooty?'")
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if p := st.chat_input("Ask a specific question..."):
            st.session_state.chat.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            st.rerun()
