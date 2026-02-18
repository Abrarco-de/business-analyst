import streamlit as st
import os
import business_ai_mvp as mvp

st.set_page_config(page_title="Advanced Business Analyst", layout="wide")

st.title("📊 Advanced Business Intelligence Dashboard")

API_KEY = os.getenv("GEMINI_API_KEY")
mvp.configure_ai(API_KEY)

uploaded_file = st.file_uploader(
    "Upload Sales / POS File (Excel or CSV)",
    type=["csv","xlsx"]
)

if uploaded_file:
    try:
        df = mvp.process_business_file(uploaded_file)

        st.subheader("📄 Cleaned Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        metrics = mvp.calculate_metrics(df)

        # Core Metrics
        st.subheader("📊 Core Financial Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Revenue (SAR)", metrics["total_revenue"])
        col2.metric("Profit (SAR)", metrics["total_profit"])
        col3.metric("Gross Margin %", metrics["gross_margin_pct"])
        col4.metric("VAT Due (15%)", metrics["vat_due"])

        st.markdown("---")

        # Detailed metrics
        st.subheader("📌 KPIs & Product Insights")

        with st.expander("📈 Top Revenue Products"):
            st.table(metrics["top_revenue_products"])

        with st.expander("💰 Top Profit Products"):
            st.table(metrics["top_profit_products"])

        if metrics["loss_making_products"]:
            with st.expander("⚠️ Loss-Making Products"):
                st.table(metrics["loss_making_products"])

        if metrics.get("total_discount") is not None:
            st.write(f"**Total Discount:** {metrics['total_discount']} SAR")
            st.write(f"**Discount Rate:** {metrics['discount_rate_pct']} %")

        with st.expander("📊 High Volume, Low Margin"):
            st.table(metrics["high_volume_low_margin"])

        st.markdown("---")

        # AI Narrative
        st.subheader("🤖 AI Business Insights")
        ai_text = mvp.generate_ai_insights(metrics)
        st.write(ai_text)

    except Exception as e:
        st.error("⚠️ Could not analyze file")
        st.error(e)

else:
    st.info("Upload a sales / POS file to get started")






