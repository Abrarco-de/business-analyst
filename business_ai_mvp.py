import streamlit as st
import pandas as pd  # <--- THIS WAS MISSING AND CAUSED THE ERROR
import google.generativeai as genai
from business_ai_mvp import process_business_file, generate_insights, configure_ai

st.set_page_config(page_title="SME Analyst Pro", layout="wide")

# API Setup
if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    ai_status = False

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload Sales Data", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # Sidebar Mapping
        st.sidebar.header("🛠️ Data Mapping")
        cols = list(df_raw.columns)
        
        # AI usually guesses the first column is product. 
        # If your product is in a different column, change it in this sidebar!
        sel_prod = st.sidebar.selectbox("Select Product/Category Column", cols, index=0)
        sel_rev = st.sidebar.selectbox("Select Revenue/Sales Column", cols, index=min(1, len(cols)-1))
        sel_qty = st.sidebar.selectbox("Select Quantity Column", cols, index=min(2, len(cols)-1))
        sel_prof = st.sidebar.selectbox("Select Profit Column (Optional)", ["None"] + cols)

        mapping = {
            "product_name": sel_prod,
            "total_amount": sel_rev,
            "quantity": sel_qty,
            "cost_price": sel_prof
        }

        res = generate_insights(df_raw, mapping)

        # Dashboard Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Total Profit", f"{res['profit']:,} SAR")
        m3.metric("Profit Margin", f"{res['margin']}%")
        m4.metric("Best Seller", res['best_seller'])

        # Sanity Check Table
        with st.expander("🔍 Verification Table"):
            st.write("Compare raw file data vs. what the app calculated:")
            check_df = pd.DataFrame({
                "Raw Value from File": df_raw[sel_rev].head(10),
                "Cleaned Number": res['df']['temp_rev'].head(10)
            })
            st.table(check_df)

        st.divider()

        # Charts and AI
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Sales by Category")
            if res['revenue'] > 0:
                chart_data = res['df'].groupby(res['name_col'])['temp_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

        with c2:
            st.subheader("AI Advice")
            if st.button("✨ Get Growth Tips"):
                if ai_status and res['revenue'] > 0:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        p = f"Revenue {res['revenue']} SAR, Top Item {res['best_seller']}. 3 tips."
                        resp = model.generate_content(p)
                        st.info(resp.text)
                    except:
                        st.error("AI Busy. Try again in 30 seconds.")


