import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# UI Style
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 12px; padding: 20px; border: 1px solid #2563EB;
    }
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# API Initialization
if "GEMINI_API_KEY" in st.secrets:
    ready = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Missing GEMINI_API_KEY in Secrets.")
    ready = False

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload Sales Data", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None and not df_raw.empty:
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        df_final = df_final.loc[:, ~df_final.columns.duplicated()].copy()
        
        res = generate_insights(df_final)

        # Dashboard Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT (15%)", f"{res['vat']:,} SAR")
        m4.metric("Cost Mode", "Estimated" if res['is_estimated'] else "Actual")

        st.divider()

        # Leaders & AI
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Revenue by Category")
            chart_data = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")
            st.info(f"🏆 **Best Seller:** {res['best_seller']}  |  💰 **Top Revenue:** {res['most_profitable']}")

        with c2:
            st.subheader("AI Growth Strategy")
            if st.button("✨ Generate Growth Advice"):
                if ready:
                    with st.spinner("Analyzing..."):
                        # India/Global Stable Models
                        for model_name in ['gemini-1.5-flash', 'gemini-pro']:
                            try:
                                model = genai.GenerativeModel(model_name)
                                prompt = f"Analyze business with {res['revenue']} SAR revenue and {res['best_seller']} as top product. Give 3 short tips."
                                response = model.generate_content(prompt)
                                if response.text:
                                    st.write(response.text)
                                    break
                            except:
                                continue
                else:
                    st.error("AI not ready. Check API Key.")
    else:
        st.error("Could not read file. Check formatting.")
