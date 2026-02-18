import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, generate_insights, configure_ai

st.set_page_config(page_title="SME Analyst Pro", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    ai_status = False

st.title("📈 SME Intelligence Analyst")

file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        st.sidebar.header("⚙️ Settings")
        all_cols = list(df_raw.columns)
        
        # Allow user to fix the mapping
        s_prod = st.sidebar.selectbox("Product Name Column", all_cols, index=0)
        s_rev = st.sidebar.selectbox("Revenue Column", all_cols, index=min(1, len(all_cols)-1))
        s_prof = st.sidebar.selectbox("Profit Column (Optional)", ["None"] + all_cols)

        mapping = {"product_name": s_prod, "total_amount": s_rev, "cost_price": s_prof}
        res = generate_insights(df_raw, mapping)

        # Dashboard Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Sales", f"{res['revenue']:,}")
        c2.metric("Total Profit", f"{res['profit']:,}")
        c3.metric("Margin", f"{res['margin']}%")
        c4.metric("Top Item", res['best_seller'])

        # --- IMPORTANT: DEBUGGER ---
        if res['revenue'] == 0:
            st.error("⚠️ Data Error: All values are 0. Python could not read your numbers.")
            st.write("Check below to see what happened:")
            debug_df = pd.DataFrame({
                "Your File Data": df_raw[s_rev].head(10),
                "How Python Cleaned It": res['df']['temp_rev'].head(10)
            })
            st.table(debug_df)

        st.divider()

        # AI Strategy
        if st.button("✨ Generate AI Growth Strategy"):
            if res['revenue'] > 0 and ai_status:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"India SME: Revenue {res['revenue']}, Top Product {res['best_seller']}. Give 3 strategies."
                    st.info(model.generate_content(prompt).text)
                except: st.error("AI Busy.")
                    




