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

file = st.file_uploader("Upload your CSV (Supermart, Sales-Data, or Retail)", type=["csv"])

if file:
    df = process_business_file(file)
    if df is not None:
        # Auto-detect headers
        auto_map = get_header_mapping(df.columns)
        
        st.sidebar.header("🛠️ Column Verification")
        st.sidebar.info("We automatically detected these columns. Adjust if needed:")
        
        cols = list(df.columns)
        # Helper to find default column index
        def find_idx(std_key, default_i):
            for k, v in auto_map.items():
                if v == std_key: return cols.index(k)
            return default_i

        sel_prod = st.sidebar.selectbox("Product/Category", cols, index=find_idx("product_name", 2))
        sel_rev = st.sidebar.selectbox("Revenue/Sales", ["Price * Quantity"] + cols, index=find_idx("total_amount", 0)+1 if "total_amount" in auto_map.values() else 0)
        sel_prof = st.sidebar.selectbox("Profit (Optional)", ["Auto-Calculate"] + cols, index=find_idx("profit", 0)+1 if "profit" in auto_map.values() else 0)

        # Build manual map
        manual_map = {"product_name": sel_prod}
        if sel_rev != "Price * Quantity": manual_map["total_amount"] = sel_rev
        else:
            # Need to find Price and Quantity for the multiplication
            manual_map["unit_price"] = auto_map.get("unit_price", cols[3] if len(cols)>3 else None)
            manual_map["quantity"] = auto_map.get("quantity", cols[4] if len(cols)>4 else None)
        
        if sel_prof != "Auto-Calculate": manual_map["profit"] = sel_prof

        # Process
        res = generate_insights(df, manual_map)

        # Show Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"{res['revenue']:,.2f} SAR")
        m2.metric("Net Profit", f"{res['profit']:,.2f} SAR")
        m3.metric("Profit Margin", f"{res['margin']}%")
        m4.metric("Best Seller", res['best_seller'])

        # Validation Table
        with st.expander("🔍 Math Verification"):
            st.write("Confirming row-by-row math:")
            st.dataframe(res['df'][[sel_prod, 'calculated_revenue']].head(10))

        st.divider()

        # AI and Chart
        left, right = st.columns([2,1])
        with left:
            st.subheader("Top Performers")
            chart_data = res['df'].groupby(res['p_col'])['calculated_revenue'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")

        with right:
            st.subheader("AI Strategic Advice")
            if st.button("✨ Generate Strategy"):
                if ai_status and res['revenue'] > 0:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        p = f"Business Revenue: {res['revenue']} SAR. Profit: {res['profit']}. Top Item: {res['best_seller']}. Give 3 growth tips."
                        st.success(model.generate_content(p).text)
                    except: st.error("AI Busy. Please wait 15 seconds.")



