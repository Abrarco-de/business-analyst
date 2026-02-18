import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, get_mapped_data, calculate_metrics, get_code_insights

st.set_page_config(page_title="MVP SME Analyst", layout="wide")

st.title("📊 Visionary SME Analyst (MVP)")
st.write("Code-based metrics for 100% accuracy and reliability.")

file = st.file_uploader("Upload your Business Data (CSV)", type=["csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # Step 1: Logic
        df_ready, p_col = get_mapped_data(df_raw)
        m = calculate_metrics(df_ready, p_col)
        
        # Step 2: Display Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"{m['revenue']:,} SAR")
        c2.metric("Total Profit", f"{m['profit']:,} SAR")
        c3.metric("ZATCA VAT (15%)", f"{m['zatca']:,} SAR")
        c4.metric("Profit Margin", f"{m['margin']}%")

        st.divider()

        # Step 3: Best Sellers
        w1, w2 = st.columns(2)
        w1.info(f"🏆 **Best Seller:** {m['best_seller']}")
        w2.success(f"💰 **Highest Profit Maker:** {m['top_profit_prod']}")

        st.divider()

        # Step 4: Logic-Based Insights
        st.subheader("💡 Automated Business Insights")
        for line in get_code_insights(m, df_ready, p_col):
            st.write(line)

        # Step 5: Chart
        st.subheader("Sales Distribution")
        chart_data = df_ready.groupby(p_col)['_calc_rev'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(chart_data)


