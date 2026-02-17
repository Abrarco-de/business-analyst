import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Analyst", layout="wide")

# API Setup
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Business Profit Analyst")

file = st.file_uploader("Upload File", type=["xlsx", "csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # Step 1: Get Mapping
        mapping = get_header_mapping(list(df_raw.columns))
        
        # Step 2: Rename Columns
        df_final = df_raw.rename(columns=mapping)
        
        # Step 3: Analyze
        metrics = generate_insights(df_final)
        
        # Step 4: Display
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue", f"{metrics['total_revenue']:,} SAR")
        c2.metric("Profit", f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}%")
        c3.metric("VAT (15%)", f"{metrics['vat_due']:,} SAR")
        
        # Help user debug if they see 0
        if metrics['total_revenue'] == 0:
            st.error("⚠️ Revenue is 0. Please check if your file has columns for 'Price' and 'Quantity'.")
            st.write("Current Mapped Columns:", mapping)
        else:
            st.success("✅ Analysis Complete!")
