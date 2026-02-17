import streamlit as st
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

# 1. Page Config
st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# 2. UI Style (Bulletproof visibility)
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 15px;
        padding: 15px;
    }
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. SECRET KEY LOGIC
# This automatically looks for the key in your Streamlit Cloud Secrets
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    configure_ai(API_KEY)
else:
    st.error("Missing Secret! Go to Streamlit Settings > Secrets and add: GEMINI_API_KEY='your_key_here'")
    st.stop()

# 4. App Logic
st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        res = generate_insights(df_final)

        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR")
        m3.metric("VAT (15%)", f"{res['vat']:,} SAR")

        # AI Strategy Section
        if st.button("✨ Generate Growth Strategy"):
            try:
                # Updated to the stable 2.5 model to fix 404
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Based on {res['revenue']} SAR revenue, give 3 growth tips."
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.error(f"API Error: {str(e)}")
