import streamlit as st
import pandas as pd
import plotly.express as px
# Top of app.py
from business_ai_mvp import configure_engines, calculate_precise_metrics, get_intelligent_answer
# 1. Config
st.set_page_config(page_title="Visionary SME AI", layout="wide")

# Initialize Session State
if "messages" not in st.session_state: st.session_state.messages = []
if "data_loaded" not in st.session_state: st.session_state.data_loaded = False

# 2. Sidebar
with st.sidebar:
    st.title("💎 Settings")
    groq_client = configure_engines(st.secrets["GEMINI_API_KEY"], st.secrets["GROQ_API_KEY"])
    if st.button("🗑️ Reset Session"):
        st.session_state.clear()
        st.rerun()

# 3. File Upload
uploaded_file = st.file_uploader("Upload Business Data (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Logic to only calculate metrics once
    if not st.session_state.data_loaded:
        df_raw = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        m, df_final = calculate_precise_metrics(df_raw)
        st.session_state.m = m
        st.session_state.df_final = df_final
        st.session_state.data_loaded = True

    # Access stored data safely
    m = st.session_state.m
    df_final = st.session_state.df_final

    # Dashboard UI
    st.markdown(f"## 📊 {uploaded_file.name} Analysis")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", f"{m['rev']:,.0f} SAR")
    c2.metric("Profit", f"{m['prof']:,.0f} SAR")
    c3.metric("Margin", f"{m['margin']}%")
    c4.metric("VAT", f"{m['vat']:,.0f} SAR")

    # Chatbot Section
    st.divider()
    st.subheader("💬 AI Business Concierge")
    chat_box = st.container(height=400)
    
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("How can I improve my margins?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_box:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing data..."):
                    response = get_intelligent_answer(groq_client, df_final, prompt, m)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

