import streamlit as st
import pandas as pd
from business_ai_mvp import configure_dual_engines, process_business_data, get_ai_response

st.set_page_config(page_title="Visionary SME AI", layout="wide")

# Sidebar Keys
with st.sidebar:
    st.header("🔑 AI Setup")
    g_client, m_client = configure_dual_engines(st.secrets["GROQ_API_KEY"], st.secrets["MISTRAL_API_KEY"])
    if not g_client: st.error("API Keys missing in secrets.toml")

# State Initialize
if "messages" not in st.session_state: st.session_state.messages = []
if "m" not in st.session_state: st.session_state.m = None

# 1. File Upload & Processing
uploaded_file = st.file_uploader("Upload Business Data", type=["csv", "xlsx"])

if uploaded_file and st.session_state.m is None:
    df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
    with st.spinner("Cleaning data..."):
        m, df_final = process_business_data(g_client, df_raw)
        st.session_state.m = m
        st.session_state.df_final = df_final

# 2. Display Advanced Metrics
if st.session_state.m:
    m = st.session_state.m
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue (SAR)", f"{m['rev']:,}")
    c2.metric("Net Profit", f"{m['prof']:,}")
    c3.metric("Best Products", m['best_product'].split(',')[0]) # Shows top 1

    # 3. Chatbot
    st.divider()
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("How can I increase my profit?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        # --- GATEKEEPER FOR SMALL TALK ---
        greetings = ["thank", "shukran", "hi", "hello", "hey"]
        if any(x in prompt.lower() for x in greetings):
            response = "You're welcome! What else can I check in your data?"
        else:
            with st.chat_message("assistant"):
                response = get_ai_response(m_client, st.session_state.m, st.session_state.df_final, prompt)
                st.write(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
