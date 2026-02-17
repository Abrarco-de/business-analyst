import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(page_title="Visionary SME Analyst", layout="wide", page_icon="📈")

# 2. Professional UI Styling (Fixes the "Invisible Text" bug)
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #F1F5F9; }
    
    /* Metric Cards - Deep Navy for high contrast */
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 15px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    /* Metric Values (Numbers) */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    /* Metric Labels (Titles) */
    [data-testid="stMetricLabel"] {
        color: #CBD5E1 !important;
        font-size: 1rem !important;
    }
    /* Metric Delta (Arrows) */
    [data-testid="stMetricDelta"] {
        background-color: transparent !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar Configuration
st.sidebar.title("🔐 Authentication")
api_key_input = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key_input:
    configure_ai(api_key_input)
else:
    st.sidebar.info("Get your key from: https://aistudio.google.com/")

# 4. Main App Interface
st.title("📈 Visionary SME Analyst")
st.markdown("##### Enterprise-grade insights for Saudi Retailers")

uploaded_file = st.file_uploader("Upload Transaction File (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("Analyzing business data..."):
        df_raw = process_business_file(uploaded_file)
        
        if df_raw is not None:
            # Get Column Mapping
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            
            # Generate Business Logic
            res = generate_insights(df_final)

            # --- ROW 1: KPI METRICS ---
            st.subheader("Financial Performance")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Revenue", f"{res['revenue']:,} SAR")
            m2.metric("Net Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
            m3.metric("VAT Due (15%)", f"{res['vat']:,} SAR")
            m4.metric("Data Status", "Estimated" if res['is_estimated'] else "Verified")

            st.divider()

            # --- ROW 2: LEADERS ---
            l1, l2 = st.columns(2)
            with l1:
                st.info(f"🏆 **Best Seller (Volume)**\n\n{res['best_seller']}")
            with l2:
                st.success(f"💰 **Most Profitable**\n\n{res['most_profitable']}")

            st.divider()

            # --- ROW 3: VISUALS & AI ---
            chart_col, ai_col = st.columns([2, 1])
            
            with chart_col:
                st.subheader("Revenue by Category")
                top_data = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(top_data, color="#1E3A8A")

            with ai_col:
                st.subheader("AI Strategy")
                if st.button("✨ Generate Growth Advice"):
                    if not api_key_input:
                        st.warning("Please provide an API Key in the sidebar.")
                    else:
                        try:
                            # Using the most stable model name
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            prompt = f"""
                            Analyze this Saudi SME data:
                            - Revenue: {res['revenue']} SAR
                            - Margin: {res['margin']}%
                            - Top Product: {res['best_seller']}
                            - Most Profitable: {res['most_profitable']}
                            
                            Provide 3 tactical growth tips for the Saudi market.
                            """
                            
                            response = model.generate_content(prompt)
                            st.write(response.text)
                        except Exception as e:
                            st.error(f"AI Error: {str(e)}")

            st.balloons()
        else:
            st.error("Format error: Could not read the uploaded file.")

