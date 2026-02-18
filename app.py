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
metrics = calculate_metrics(df_final)

st.subheader("📊 Business Metrics")
st.metric("Revenue", f"{metrics['total_revenue']} SAR")
st.metric("Profit", f"{metrics['total_profit']} SAR")
st.metric("Margin", f"{metrics['gross_margin_pct']} %")
st.metric("VAT Due", f"{metrics['vat_due']} SAR")

st.subheader("🤖 AI Insights")
st.write(generate_ai_insights(metrics))

    except Exception as e:
        st.error(str(e))





