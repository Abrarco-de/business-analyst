import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

# Setup
API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Saudi SME Analyst")
file = st.file_uploader("Upload POS Data")

if file:
    df_raw = process_business_file(file)
    mapping = get_header_mapping(list(df_raw.columns))
    df_final = df_raw.rename(columns=mapping)
    
    stats = generate_insights(df_final)
    st.metric("Total Profit", f"{stats['total_profit']} SAR")








