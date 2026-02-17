import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide", page_icon="📈")

# --- UI STYLING (FIXED INVISIBLE TEXT) ---
st.markdown("""
    <style>
    /* Card Container */
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 15px !important;
        padding: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
    }
    /* Metric Value (The big numbers) */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }
    /* Metric Label (The titles) */
    [data-testid="stMetricLabel"] {
        color: #E2E8F0 !important;
    }
    /* Metric Delta (The green/red arrows) */
    [data-testid="stMetricDelta"] {
        color: #4ADE80 !important;
        background-color: rgba(0,0,0,0) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# API Setup
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("📈 Visionary SME Analyst")
st.markdown("##### Professional Business Intelligence for Saudi Retailers")

file = st.file_uploader("Upload Transaction File (CSV/Excel)", type=["csv", "xlsx"])

if file:
    with st.spinner("Analyzing Business performance..."):
        df_raw = process_business_file(file)
        if df_raw is not None:
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            res = generate_insights(df_final)

            # --- TOP ROW: KPI CARDS ---
            st.subheader("Executive Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"{res['revenue']:,} SAR")
            c2.metric("Net Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
            c3.metric("ZATCA VAT (15%)", f"{res['vat']:,} SAR")
            c4.metric("Status", "Estimated Cost" if res['is_estimated'] else "Verified Data")

            st.divider()

            # --- MIDDLE ROW: LEADERS ---
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"🏆 **Best Seller (Volume):** \n\n {res['best_seller']}")
            with col_b:
                st.success(f"💰 **Most Profitable (Value):** \n\n {res['most_profitable']}")

            st.divider()

            # --- BOTTOM ROW: CHARTS ---
            chart_col, debug_col = st.columns([2, 1])
            with chart_col:
                st.subheader("Revenue by Product Category")
                top_10 = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(top_10, color="#1E3A8A")

            with debug_col:
                st.subheader("AI Intelligence Log")
                with st.expander("View Column Mapping"):
                    st.json(mapping)
                
                if st.button("✨ Generate AI Growth Strategy"):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"Business Revenue: {res['revenue']} SAR. Best Product: {res['best_seller']}. Most profitable: {res['most_profitable']}. Give 3 specific strategies for a Saudi SME to grow."
                        response = model.generate_content(prompt)
                        st.write(response.text)
                    except Exception as e:
                        st.error("AI strategy is temporarily unavailable. Check your API key.")
            
            st.balloons()


