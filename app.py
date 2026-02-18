import streamlit as st
import pandas as pd
# Ensure this line matches exactly the functions in business_ai_mvp.py
from business_ai_mvp import configure_engines, calculate_precise_metrics, get_intelligent_answer

st.set_page_config(page_title="Visionary SME AI", layout="wide")

# Initialize state
if "m" not in st.session_state:
    st.session_state.m = None
    st.session_state.df_final = None

# Sidebar Setup
with st.sidebar:
    st.header("🔑 API Keys")
    # Make sure these are set in your .streamlit/secrets.toml or Streamlit Cloud
    groq_client = configure_engines(st.secrets["GEMINI_API_KEY"], st.secrets["GROQ_API_KEY"])

# File Upload
uploaded_file = st.file_uploader("Upload Data", type=["csv", "xlsx"])

if uploaded_file:
    if st.session_state.m is None:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('csv') else pd.read_excel(uploaded_file)
        m, df_final = calculate_precise_metrics(df)
        st.session_state.m = m
        st.session_state.df_final = df_final
    
    m = st.session_state.m
    df_final = st.session_state.df_final

    # Display Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"{m['rev']:,} SAR")
    c2.metric("Profit", f"{m['prof']:,} SAR")
    c3.metric("Margin", f"{m['margin']}%")

    # Chat
    if prompt := st.chat_input("Ask about your data..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                answer = get_intelligent_answer(groq_client, df_final, prompt, m)
                st.write(answer)
