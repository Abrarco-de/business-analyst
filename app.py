import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, get_mapped_data, calculate_metrics, get_code_insights

st.set_page_config(page_title="MVP SME Analyst", layout="wide")

st.title("📈 Visionary SME Analyst")
st.markdown("### Data-Driven Metrics & Automated Insights")

file = st.file_uploader("Upload your sales data (CSV)", type=["csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # 1. Processing
        df_ready, p_col = get_mapped_data(df_raw)
        m = calculate_metrics(df_ready, p_col)
        
        # 2. KPI Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"{m['revenue']:,} SAR")
        c2.metric("Total Profit", f"{m['profit']:,} SAR")
        c3.metric("ZATCA VAT (15%)", f"{m['vat']:,} SAR")
        c4.metric("Profit Margin", f"{m['margin']}%")

        st.divider()

        # 3. Winners Row
        w1, w2 = st.columns(2)
        with w1:
            st.subheader("🏆 Best Seller (Revenue)")
            st.info(f"**{m['best_seller']}**")
        with w2:
            st.subheader("💰 Highest Profit Making Product")
            st.success(f"**{m['top_profit_prod']}**")

        st.divider()

        # 4. Code-Based Automated Insights (No AI Busy Errors here!)
        st.subheader("📊 Automated Business Insights")
        insights = get_code_insights(m, df_ready, p_col)
        for insight in insights:
            st.write(insight)

        # 5. Visual Performance
        st.subheader("Product Performance (Revenue)")
        chart_data = df_ready.groupby(p_col)['_calc_rev'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(chart_data, color="#004aad")


