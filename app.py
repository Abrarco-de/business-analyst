import streamlit as st
import os
import business_ai_mvp as mvp

st.set_page_config(page_title="Business Analyst MVP", layout="wide")

# ---------- CONFIG ----------
API_KEY = os.getenv("GEMINI_API_KEY")
mvp.configure_ai(API_KEY)

st.title("📊 AI Business Analyst")

uploaded_file = st.file_uploader(
    "Upload your POS / Sales file",
    type=["csv", "xlsx"]
)

# ---------- MAIN FLOW ----------
if uploaded_file is not None:
    try:
        # Step 1: Clean & normalize
        df_final = mvp.process_business_file(uploaded_file)

        st.subheader("📄 Cleaned Data Preview")
        st.dataframe(df_final.head(20))

        # Step 2: Metrics
        metrics = mvp.calculate_metrics(df_final)

        st.subheader("📈 Business Metrics")
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Revenue", f"{metrics['total_revenue']} SAR")
        c2.metric("Profit", f"{metrics['total_profit']} SAR")
        c3.metric("Margin %", f"{metrics['gross_margin_pct']}%")
        c4.metric("VAT Due", f"{metrics['vat_due']} SAR")

        # Step 3: AI Insights
        st.subheader("🤖 AI Business Insights")
        insight_text = mvp.generate_ai_insights(metrics)
        st.write(insight_text)

    except Exception as e:
        st.error("❌ Error processing file")
        st.code(str(e))






