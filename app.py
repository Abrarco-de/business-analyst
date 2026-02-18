import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

if "m" not in st.session_state: st.session_state.m = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

g_client, m_client = configure_dual_engines(st.secrets["GROQ_API_KEY"], st.secrets["MISTRAL_API_KEY"])

st.title("📊 Visionary SME Dashboard")

# Upload Section
if st.session_state.m is None:
    uploaded_file = st.file_uploader("Upload Data", type=["csv", "xlsx"])
    if uploaded_file:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        st.session_state.m, _ = process_business_data(g_client, df_raw)
        st.rerun()
else:
    with st.sidebar:
        if st.button("Reset"):
            st.session_state.m = None
            st.rerun()

# Dashboard Rendering
if st.session_state.m:
    m = st.session_state.m
    
    # Financial Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"{m['total_revenue']:,} SAR")
    c2.metric("Total Profit", f"{m['total_profit']:,} SAR")
    c3.metric("Highest Margin Item", m['top_margin_item'])
    c4.metric("Lowest Margin Item", m['bot_margin_item'])

    st.divider()

    # Sorted Tables Row
    t1, t2 = st.columns(2)
    with t1:
        st.subheader("📉 Least Margin Products (Sorted)")
        # Show as a list for clarity
        for item in m['bot_margin_list'].split(", "):
            st.error(item)
            
    with t2:
        st.subheader("📈 Highest Margin Products (Sorted)")
        for item in m['top_margin_list'].split(", "):
            st.success(item)

    # Chatbot Popover
    st.markdown("""<style>.stPopover {position: fixed; bottom: 30px; right: 30px;}</style>""", unsafe_allow_html=True)
    with st.popover("💬 Chat with Strategist"):
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if p := st.chat_input("Ask about your margins..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            ans = get_ai_response(m_client, st.session_state.m, p)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            st.rerun()
