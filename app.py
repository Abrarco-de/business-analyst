import streamlit as st
from business_ai_mvp import process_business_file, generate_insights



st.set_page_config(page_title="AI Business Analyst")

st.title("📊 AI Business Analyst (MVP)")
st.write("Upload CSV or ZATCA XML to get instant insights.")

uploaded_file = st.file_uploader(
    "Upload file",
    type=["csv", "xml"]
)

if uploaded_file:
    try:
        df = process_business_file(uploaded_file)
        insights = generate_insights(df)

        st.success("Analysis Complete")

        st.metric("Total Revenue", insights["total_revenue"])
        st.metric("Total Profit", insights["total_profit"])
        st.metric("Profit Margin (%)", insights["profit_margin"])

        st.subheader("Top Products")
        st.json(insights["top_products"])

        if insights["loss_products"]:
            st.subheader("Loss-Making Products")
            st.write(insights["loss_products"])

    except Exception as e:
        st.error(str(e))



