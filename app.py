import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    ai_status = False

st.title("📊 SME Business Intelligence (ZATCA Compliant)")

file = st.file_uploader("Upload your CSV", type=["csv"])

if file:
    df = process_business_file(file)
    if df is not None:
        auto_map = get_header_mapping(df.columns)
        st.sidebar.header("⚙️ Column Mapping")
        cols = list(df.columns)

        sel_prod = st.sidebar.selectbox("Product Column", cols, index=0)
        sel_rev = st.sidebar.selectbox("Revenue Column", ["Calculate (Price*Qty)"] + cols, index=0)
        sel_prof = st.sidebar.selectbox("Profit Column", ["Auto-Estimate"] + cols, index=0)

        m_map = {"product_name": sel_prod}
        if sel_rev != "Calculate (Price*Qty)": m_map["total_amount"] = sel_rev
        if sel_prof != "Auto-Estimate": m_map["profit"] = sel_prof

        res = generate_insights(df, m_map)

        # Dashboard Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"{res['revenue']:,.2f} SAR")
        m2.metric("Total Profit", f"{res['profit']:,.2f} SAR")
        m3.metric("ZATCA VAT (15%)", f"{res['zatca_vat']:,.2f} SAR")

        st.divider()

        c1, c2 = st.columns(2)
        c1.info(f"🏆 **Best Seller (Revenue):** {res['best_seller']}")
        c2.success(f"💰 **Most Profitable Item:** {res['most_profitable_prod']}")

        st.divider()

        # Visuals
        left, right = st.columns([2,1])
        with left:
            st.subheader("Product Performance (Revenue)")
            chart_data = res['df'].groupby(res['p_col'])['calculated_revenue'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data)

        with right:
            st.subheader("AI Growth Strategy")
            if st.button("✨ Ask Gemini"):
                if ai_status and res['revenue'] > 0:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Revenue: {res['revenue']} SAR. Top Profit Maker: {res['most_profitable_prod']}. 3 growth tips."
                    st.write(model.generate_content(prompt).text)


