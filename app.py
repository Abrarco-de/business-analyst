import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Pro Analyst", layout="wide")

# Replace with your actual key or use Streamlit Secrets
API_KEY = "YOUR_GEMINI_API_KEY" 
is_ai_ready = configure_ai(API_KEY)

st.title("🇸🇦 Saudi SME Analyst Pro")

file = st.file_uploader("Upload Sales Data", type=["csv", "xlsx"])

if file and is_ai_ready:
    df_raw = process_business_file(file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df = df_raw.rename(columns=mapping)
        metrics = generate_insights(df)

        # Dashboard KPI Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", f"{metrics['total_revenue']:,} SAR", f"{metrics['growth_pct']}% Growth")
        c2.metric("Net Profit", f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}% Margin")
        c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
        c4.metric("Top Product", metrics['top_product'])

        st.divider()
        st.subheader("Revenue Analysis")
        # Bar Chart
        prod_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
        chart_data = df.groupby(prod_col)['calc_rev'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(chart_data)
    else:
        st.error("Error processing file format.")
elif not is_ai_ready:
    st.warning("Please configure your Gemini API Key to enable AI mapping.")
