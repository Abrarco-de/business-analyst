import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, generate_insights

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI Business Analyst",
    page_icon="📊",
    layout="centered"
)

# ================= UI =================
st.title("📊 AI Business Analyst for Small Businesses")
st.write(
    "Upload your **sales / POS file** (CSV or Excel). "
    "The AI will clean the data and generate business insights automatically."
)

# ================= FILE UPLOAD =================
uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file:
    try:
        with st.spinner("🔍 Cleaning and understanding your data..."):
            df = process_business_file(uploaded_file)

        st.success("✅ File processed successfully")

        # ================= PREVIEW =================
        st.subheader("📄 Cleaned Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # ================= INSIGHTS =================
        if st.button("📈 Generate Business Insights"):
            with st.spinner("📊 Generating insights..."):
                insights = generate_insights(df)

            st.subheader("📊 Business Insights")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Revenue (SAR)", insights["total_revenue"])
            col2.metric("Total Profit (SAR)", insights["total_profit"])
            col3.metric("Profit Margin (%)", insights["profit_margin_percent"])

            # ================= TOP PRODUCTS =================
            if insights["top_products"]:
                st.subheader("🔥 Top Selling Products")
                top_df = pd.DataFrame(
                    insights["top_products"].items(),
                    columns=["Product", "Revenue"]
                )
                st.table(top_df)

            # ================= LOSS PRODUCTS =================
            if insights["loss_products"]:
                st.subheader("⚠️ Loss-Making P








