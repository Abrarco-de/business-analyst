import streamlit as st
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# API Configuration
if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Set API Key in Secrets!")
    ai_status = False

st.title("📈 Visionary SME Analyst")

file = st.file_uploader("Upload Sales File", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df_mapped = df_raw.rename(columns=mapping)
        res = generate_insights(df_mapped)

        # DEBUG SECTION (Helpful for you to see why it might be 0)
        with st.expander("🛠️ System Debug: How I see your data"):
            st.write("Columns detected:", list(df_raw.columns))
            st.write("Matched Schema:", mapping)
            st.dataframe(df_mapped.head(3))

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}%")
        m3.metric("VAT", f"{res['vat']:,} SAR")
        m4.metric("Status", "Calculated")

        st.divider()

        # AI Advice
        if st.button("✨ Get AI Growth Strategy"):
            if res['revenue'] > 0:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Business has {res['revenue']} SAR revenue. Best product: {res['best_seller']}. Give 3 India-specific growth tips."
                try:
                    resp = model.generate_content(prompt)
                    st.success(resp.text)
                except: st.error("AI busy. Try again.")
            else:
                st.warning("Cannot give advice because Revenue is 0. Please check the 'System Debug' above to see if columns matched.")
        




