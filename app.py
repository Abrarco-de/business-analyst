import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# 1. UI STYLING (Forced Visibility)
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 12px; padding: 15px;
    }
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. API SETUP
if "GEMINI_API_KEY" in st.secrets:
    configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Add GEMINI_API_KEY to Secrets.")

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload Transaction File", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    
    if df_raw is not None and not df_raw.empty:
        # Get mapping and fix the "0" values issue
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        
        # Ensure we don't have duplicate columns after renaming
        df_final = df_final.loc[:, ~df_final.columns.duplicated()].copy()
        
        res = generate_insights(df_final)

        # Performance Summary
        st.subheader("Performance Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT (15%)", f"{res['vat']:,} SAR")
        m4.metric("Cost Mode", "Estimated" if res['is_estimated'] else "Actual")

        st.divider()

        # Leaderboard
        l1, l2 = st.columns(2)
        l1.info(f"🏆 **Best Seller (Volume):**\n\n{res['best_seller']}")
        l2.success(f"💰 **Top Revenue Source:**\n\n{res['most_profitable']}")

        # Charts and AI
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Sales by Category")
            # Force the name_col to be a string to avoid errors
            chart_data = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")
        
       with c2:
            st.subheader("AI Growth Strategy")
            if st.button("✨ Generate Strategy"):
                # Define potential models to try
                models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
                success = False
                
                for model_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        prompt = f"Analyze Saudi SME: Rev {res['revenue']} SAR. Give 3 short tips."
                        response = model.generate_content(prompt)
                        
                        if response.text:
                            st.info(response.text)
                            success = True
                            break # Stop if we get a response
                    except:
                        continue # Try the next model if this one fails
                
                if not success:
                    st.error("AI is currently busy or region-restricted. Please check your API billing/quota at AI Studio.")
    else:
        st.error("File is empty or corrupted.")



