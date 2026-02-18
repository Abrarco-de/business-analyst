import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, gemini_schema_mapper, generate_logic_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    configure_ai(st.secrets["GEMINI_API_KEY"])

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload your sales file (CSV)", type=["csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # Step 1: Gemini decides the schema (Architecture)
        with st.spinner("Gemini is mapping your data structure..."):
            schema = gemini_schema_mapper(df_raw.columns)
        
        # Step 2: Python calculates the insights (Logic Engine)
        res = generate_logic_insights(df_raw, schema)

        # Step 3: Display
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"{res['revenue']:,.2f} SAR")
        c2.metric("Total Profit", f"{res['profit']:,.2f} SAR")
        c3.metric("ZATCA VAT (15%)", f"{res['vat']:,.2f} SAR")

        st.divider()
        
        w1, w2 = st.columns(2)
        w1.info(f"🏆 **Best Seller:** {res['best_seller']}")
        w2.success(f"💰 **Most Profitable Product:** {res['most_profitable']}")

        st.divider()
        
        st.subheader("💡 Automated Business Insights")
        for line in res['insights']:
            st.write(line)

        st.subheader("Top 10 Product Sales")
        chart_data = res['df'].groupby(res['p_col'])['_rev'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(chart_data)


