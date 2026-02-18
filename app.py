import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, generate_insights

import os


st.write("CWD:", os.getcwd())
st.write("FILES:", os.listdir())

st.write("Files in directory:", os.listdir())
df = business_mvp.process_file(uploaded_file)
metrics = business_mvp.generate_metrics(df)

st.set_page_config(
    page_title="SME Business Intelligence",
    layout="wide"
)

st.title("📊 SME Business Intelligence Dashboard")
st.caption("Professional business analytics for small & medium enterprises")

uploaded_file = st.file_uploader(
    "Upload Sales / POS File (CSV or Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    try:
        df = process_file(uploaded_file)
        metrics = generate_metrics(df)

        # ================= METRICS =================
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", f"{metrics['total_revenue']:,}")
        c2.metric("Profit", f"{metrics['total_profit']:,}")
        c3.metric("Margin %", f"{metrics['gross_margin']}%")
        c4.metric("VAT (15%)", f"{metrics['vat']:,}")

        st.divider()

        # ================= BUSINESS INSIGHTS =================
        st.subheader("📌 Key Insights")
        st.write(f"• **Top Revenue Product:** {metrics['top_revenue_product']}")
        st.write(f"• **Top Profit Product:** {metrics['top_profit_product']}")
        st.write(
            f"• **Revenue Concentration:** "
            f"{metrics['revenue_concentration']}% from top product"
        )

        if metrics["revenue_concentration"] > 60:
            st.warning("⚠ High dependency on a single product")

        # ================= CHART =================
        st.subheader("📈 Product Revenue Distribution")
        st.bar_chart(
            metrics["product_perf"]["revenue"].head(10),
            use_container_width=True
        )

        # ================= LOSS MAKERS =================
        if not metrics["loss_products"].empty:
            st.subheader("❌ Loss Making Products")
            st.dataframe(metrics["loss_products"])

        # ================= RAW DATA =================
        with st.expander("🔍 View Cleaned Data"):
            st.dataframe(df)

    except Exception as e:
        st.error("Error processing file")
        st.exception(e)
else:
    st.info("Upload a file to begin analysis")




