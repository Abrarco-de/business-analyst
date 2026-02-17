import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

# Page Config for professional look
st.set_page_config(page_title="Visionary SME Analyst", layout="wide", page_icon="📈")

# Professional UI Styling
st.markdown("""
    <style>
    /* This targets the container of the metric */
    [data-testid="stMetric"] {
        background-color: #1E3A8A; /* Deep Blue background */
        color: white !important;    /* Force white text */
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* This ensures the label (title) is also visible */
    [data-testid="stMetricLabel"] {
        color: #E2E8F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)  # Fixed parameter name

# API Setup
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("📈 Visionary SME Analyst")
st.markdown("##### Empowering Saudi SMEs with AI-Driven Financial Clarity")

uploaded_file = st.file_uploader("Drop your transaction file here", type=["csv", "xlsx"])

if uploaded_file:
    df_raw = process_business_file(uploaded_file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        res = generate_insights(df_final)

        # --- ROW 1: PRIMARY METRICS ---
        st.markdown("### Financial Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Net Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT Due (ZATCA)", f"{res['vat']:,} SAR")
        m4.metric("Data Status", "Estimated Cost" if res['is_estimated'] else "Verified Data")

        st.divider()

        # --- ROW 2: LEADERBOARD CARDS ---
        st.markdown("### Performance Leaders")
        l1, l2 = st.columns(2)
        with l1:
            st.success(f"🏆 **Best Selling Product:** \n\n {res['best_seller']}")
        with l2:
            st.info(f"💰 **Highest Profit Maker:** \n\n {res['most_profitable']}")

        st.divider()

        # --- ROW 3: VISUALS & LOG ---
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Sales Distribution")
            top_10 = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(top_10, color="#1E3A8A")

        with col_right:
            st.subheader("AI Smart Mapping")
            with st.expander("Show Column Logic"):
                st.json(mapping)
            
            # AI Advice Trigger
            if st.button("✨ Generate AI Growth Strategy"):
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                prompt = f"Business Revenue: {res['revenue']} SAR. Best Product: {res['best_seller']}. Give 3 specific strategies for a Saudi SME to double their profit."
                advice = model.generate_content(prompt)
                st.write(advice.text)

        st.balloons()





