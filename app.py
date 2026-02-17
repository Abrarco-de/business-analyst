import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Saudi SME Analyst", layout="wide")

# AI Key (Ensure this is set in your environment or secrets)
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 SME Profit Intelligence")

file = st.file_uploader("Upload POS Data (CSV/Excel)", type=["xlsx", "csv"])

if file:
    with st.spinner("AI analyzing your data..."):
        df_raw = process_business_file(file)
        
        if df_raw is not None:
            # 1. Map and Rename
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            
            # 2. Generate Results
            metrics = generate_insights(df_final)
            
            # 3. Metrics Display
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR")
            
            prof_label = "Estimated Profit (65% COGS)" if metrics['is_estimated_cost'] else "Net Profit"
            c2.metric(prof_label, f"{metrics['total_profit']:,} SAR", delta=f"{metrics['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            
            st.divider()
            
            # 4. Debug/Verification
            with st.expander("Show AI Column Mapping"):
                st.write("If the numbers look wrong, ensure your columns are mapped correctly here:")
                st.json(mapping)
                st.dataframe(df_final.head())
        else:
            st.error("Could not read the file. Please check the format.")




