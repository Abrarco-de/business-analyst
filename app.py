import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    ai_status = False

st.title("📊 SME Business Intelligence")
st.write("Calculations optimized for Retail and Grocery datasets.")

file = st.file_uploader("Upload Sales CSV", type=["csv"])

if file:
    df = process_business_file(file)
    if df is not None:
        # Step 1: Auto-Detect Columns
        auto_map = get_header_mapping(df.columns)
        cols = list(df.columns)

        # Step 2: Sidebar Settings (Pre-filled with Auto-Detection)
        st.sidebar.header("⚙️ Column Mapping")
        
        def get_default(std_key, fallback_idx):
            for k, v in auto_map.items():
                if v == std_key: return cols.index(k)
            return fallback_idx

        sel_prod = st.sidebar.selectbox("Product/Category Name", cols, index=get_default("product_name", 0))
        
        # Smart default for Revenue
        rev_default_idx = 0 # Default to "Calculate"
        if "total_amount" in auto_map.values():
            rev_default_idx = cols.index([k for k,v in auto_map.items() if v=="total_amount"][0]) + 1

        sel_rev = st.sidebar.selectbox("Revenue/Sales Column", ["Calculate (Price * Qty)"] + cols, index=rev_default_idx)
        sel_prof = st.sidebar.selectbox("Profit Column", ["Auto-Estimate (25%)"] + cols, index=get_default("profit", -1)+1 if "profit" in auto_map.values() else 0)

        # Build final mapping
        m_map = {"product_name": sel_prod}
        if sel_rev != "Calculate (Price * Qty)":
            m_map["total_amount"] = sel_rev
        else:
            m_map["unit_price"] = [k for k,v in auto_map.items() if v=="unit_price"][0] if "unit_price" in auto_map.values() else None
            m_map["quantity"] = [k for k,v in auto_map.items() if v=="quantity"][0] if "quantity" in auto_map.values() else None

        if sel_prof != "Auto-Estimate (25%)":
            m_map["profit"] = sel_prof

        # Step 3: Run Insights
        res = generate_insights(df, m_map)

        # Step 4: Display Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Revenue", f"{res['revenue']:,.2f} SAR")
        m2.metric("Net Profit", f"{res['profit']:,.2f} SAR")
        m3.metric("ZATCA VAT (15%)", f"{res['zatca_vat']:,.2f} SAR")

        st.divider()

        # Step 5: High-Level Winners
        c1, c2 = st.columns(2)
        c1.info(f"🏆 **Best Seller (Revenue):** {res['best_seller']}")
        c2.success(f"💰 **Highest Profit Maker:** {res['most_profitable_prod']}")

        st.divider()

        # Step 6: Visuals and AI
        left, right = st.columns([2,1])
        with left:
            st.subheader("Top 10 Products by Revenue")
            chart_data = res['df'].groupby(res['p_col'])['calculated_revenue'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")
        
        with right:
            st.subheader("AI Strategic Advice")
            if st.button("✨ Ask Gemini"):
                if ai_status and res['revenue'] > 0:
                    with st.spinner("Analyzing..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"Revenue: {res['revenue']} SAR, Top Item: {res['best_seller']}, Most Profitable: {res['most_profitable_prod']}. Give 3 growth tips."
                            st.write(model.generate_content(prompt).text)
                        except: st.error("AI Busy. Try in 10s.")
                else:
                    st.warning("Ensure Revenue > 0 and AI Key is valid.")


