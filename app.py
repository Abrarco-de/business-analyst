import streamlit as st
import os
# Make sure this matches the filename business_ai_mvp.py
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Saudi SME Intelligence", layout="wide")

# API Key
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Business Profit Analyst")

file = st.file_uploader("Upload POS File", type=["xlsx", "csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        
        metrics = generate_insights(df_final)
        
        # Display Results
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue", f"{metrics['total_revenue']} SAR")
        c2.metric("Profit", f"{metrics['total_profit']} SAR")
        c3.metric("VAT (15%)", f"{metrics['vat_due']} SAR")
        
        st.success(f"Analysis complete! Your margin is {metrics['margin']}%")







