import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

# 1. Initialize Session
if "m" not in st.session_state: st.session_state.m = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# 2. Setup Engines
g_client, m_client = configure_dual_engines(st.secrets["GROQ_API_KEY"], st.secrets["MISTRAL_API_KEY"])

st.title("📊 Visionary SME Dashboard")

# 3. Centralized Uploader
if st.session_state.m is None:
    st.info("👋 Welcome! Please upload your business data to begin.")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        st.session_state.m, _ = process_business_data(g_client, df_raw)
        st.rerun()
else:
    with st.sidebar:
        if st.button("🗑️ Reset and Upload New File"):
            st.session_state.m = None
            st.rerun()

# 4. Dashboard Display
if st.session_state.m:
    m = st.session_state.m
    
    # Financial Row
    st.subheader("💰 Financial Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Revenue", f"{m.get('total_revenue', 0):,} SAR")
    c2.metric("Total Profit", f"{m.get('total_profit', 0):,} SAR")
    c3.metric("Gross Margin", f"{m.get('gross_margin_pct', 0)}%")
    c4.metric("VAT (15%)", f"{m.get('vat_due', 0):,} SAR")
    c5.metric("Avg Trans.", f"{m.get('avg_transaction', 0):,} SAR")

    st.divider()

    # Operations Row
    st.subheader("📦 Operations")
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Units Sold", f"{m.get('total_units', 0):,}")
    o2.metric("Rev Per Unit", f"{m.get('rev_per_unit', 0):,} SAR")
    o3.info(f"📈 **High Margin:**\n{m.get('top_margin_item', 'N/A')}")
    o4.warning(f"📉 **Least Margin:**\n{m.get('bot_margin_item', 'N/A')}")

    # Sorted Lists Row
    st.divider()
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("📉 Least Margin Items (Sorted)")
        for item in m.get('bot_margin_list', "N/A").split(", "):
            st.error(item)
    with t2:
        st.subheader("📈 Top Margin Items (Sorted)")
        for item in m.get('top_margin_list', "N/A").split(", "):
            st.success(item)

    # 5. Floating Chatbot
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Chat with AI Strategist"):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Ask about your margins..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, m, p)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()
