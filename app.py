import streamlit as st
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Growth Analyst", layout="wide")

# Market-Ready UI
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E3A8A !important; border-radius: 10px; padding: 15px; }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# API Secret Check
if "GEMINI_API_KEY" in st.secrets:
    ai_ready = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.warning("Add GEMINI_API_KEY to Secrets to enable AI tips.")
    ai_ready = False

st.title("📈 SME Growth Analyst")
st.write("Professional Analysis for Retail & Business Data")

file = st.file_uploader("Upload Transaction File", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # Hybrid Logic Start: 
        # 1. Rule-based Mapping
        mapping = get_header_mapping(list(df_raw.columns))
        df_mapped = df_raw.rename(columns=mapping)
        
        # 2. Hardcoded Calculations
        res = generate_insights(df_mapped)

        # UI Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"{res['revenue']:,} SAR")
        col2.metric("Net Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        col3.metric("VAT (15%)", f"{res['vat']:,} SAR")
        col4.metric("Cost Mode", "AI Estimate" if res['is_estimated'] else "Verified")

        st.divider()

        # Visuals and AI
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
    st.subheader("Revenue by Category")
    
    # ADVANCED LOGIC: Check if data exists to avoid crashes
    if not res['df'].empty:
        try:
            # Ensure the grouping column exists and sum the revenue
            chart_data = (
                res['df']
                .groupby(res['name_col'])['temp_rev']
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            
            # Professional Bar Chart
            st.bar_chart(chart_data, color="#1E3A8A")
            
            # Add a small summary text below the chart
            st.caption(f"Showing top categories based on {res['name_col']}")
        except Exception as e:
            st.warning("Could not generate chart. Please check if the product column is correct.")
    else:
        st.info("No data available to display chart.")
        with c_right:
            st.subheader("AI Strategic Advice")
            if st.button("✨ Get Growth Tips"):
                if ai_ready:
                    with st.spinner("Generating insights..."):
                        # Permanent 404 Fix: Fallback list
                        for m_name in ['gemini-1.5-flash', 'gemini-pro']:
                            try:
                                model = genai.GenerativeModel(m_name)
                                prompt = f"Business Summary: {res['revenue']} SAR Revenue, Best Product: {res['best_seller']}. Give 3 short tactical growth tips for this SME."
                                response = model.generate_content(prompt)
                                st.success(response.text)
                                break
                            except: continue
                else: st.error("AI is not configured.")

    else: st.error("Unsupported file format.")



