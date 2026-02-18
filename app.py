import streamlit as st
import business_ai_mvp as mvp

st.set_page_config(
    page_title="Saudi SME Intelligence",
    layout="wide"
)

st.title("🇸🇦 SME Business Intelligence Dashboard")

uploaded_file = st.file_uploader(
    "Upload POS / Sales File (CSV or Excel)",
    type=["csv", "xlsx"]
)

if uploaded_file:
    try:
        df = mvp.process_business_file(uploaded_file)

        st.subheader("📄 Data Preview")
        st.dataframe(df.head(20), use_container_width=True)

        metrics = mvp.generate_insights(df)

        st.subheader("📊 Key Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue (SAR)", metrics["total_revenue"])
        c2.metric("Profit (SAR)", metrics["total_profit"])
        c3.metric("Margin (%)", metrics["margin"])
        c4.metric("VAT 15% (SAR)", metrics["vat"])

        st.subheader("🔥 Top Profitable Products")
        st.table(metrics["top_products"])

        st.subheader("⚠️ Loss-Making Products")
        st.table(metrics["loss_products"])

    except Exception as e:
        st.error(str(e))




