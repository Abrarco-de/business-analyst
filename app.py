import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

# 1. UI Configuration
st.set_page_config(page_title="Visionary SME AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0F1E; color: #E2E8F0; }
    [data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        padding: 1.5rem;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. State Management
if "messages" not in st.session_state: st.session_state.messages = []
if "data_ready" not in st.session_state: st.session_state.data_ready = False

# 3. Engines
g_client, m_client = configure_dual_engines(st.secrets["GROQ_API_KEY"], st.secrets["MISTRAL_API_KEY"])

# 4. Main Interface
st.title("💎 Visionary SME AI")
st.caption("Dual-Agent Strategy: Groq Cleaning + Mistral Intelligence")

uploaded_file = st.file_uploader("Upload Daily Sales/Finance File", type=["csv", "xlsx"])

if uploaded_file:
    if not st.session_state.data_ready:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        with st.spinner("Agents are syncing data..."):
            m, df_final = process_business_data(g_client, df_raw)
            st.session_state.m = m
            st.session_state.df_final = df_final
            st.session_state.data_ready = True

    m = st.session_state.m
    
    # Advanced Metrics Grid
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue (SAR)", f"{m['rev']:,}")
    c2.metric("Net Profit", f"{m['prof']:,}")
    c3.metric("Margin %", f"{m['margin']}%")
    c4.metric("VAT Liability", f"{m['vat']:,}")

    st.divider()

    # Chatbot with Data Exchange
    st.subheader("💬 Executive Consulting")
    chat_container = st.container(height=400, border=True)

    for msg in st.session_state.messages:
        with chat_container.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Ask: Why is my margin low? or How to increase sales?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"): st.markdown(prompt)
        
        with chat_container.chat_message("assistant"):
            with st.spinner("Mistral is thinking..."):
                response = get_ai_response(m_client, m, st.session_state.df_final, prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
