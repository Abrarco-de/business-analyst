import streamlit as st
import pandas as pd
from business_ai_mvp import *

st.set_page_config(page_title="Visionary SME Analyst", layout="wide", page_icon="📈")

# Load Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

groq_client = configure_engines(GEMINI_KEY, GROQ_KEY)

# Custom CSS for a professional look
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Visionary SME Analyst")
st.subheader("Hybrid AI Dashboard: Gemini + Llama 3")

uploaded_file = st.file_uploader("Upload your sales data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df_raw = process_business_file(uploaded_file)
    
    if df_raw is not None:
        with st.status("Analyzing Data Structure...") as status:
            # 1. Schema Mapping (Gemini)
            st.write("Detecting columns...")
            schema = gemini_get_schema(df_raw.columns)
            
            if schema:
                # 2. Precise Calculation (Python)
                st.write("Calculating business metrics...")
                metrics, df_final = calculate_precise_metrics(df_raw, schema)
                status.update(label="Analysis Complete!", state="complete", expanded=False)
                
                # --- Metrics Display ---
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Revenue", f"{metrics['rev']:,} SAR")
                m2.metric("Total Profit", f"{metrics['prof']:,} SAR")
                m3.metric("ZATCA VAT (15%)", f"{metrics['vat']:,} SAR")

                st.divider()
                
                # --- Top Performers ---
                w1, w2 = st.columns(2)
                with w1:
                    st.info(f"🏆 **Best Seller (By Volume):**\n\n{metrics['best_seller']}")
                with w2:
                    st.success(f"💰 **Highest Profit Maker:**\n\n{metrics['top_profit_prod']}")

                st.divider()

                # --- AI Strategy (Groq) ---
                st.subheader("💡 Strategic Insights (Powered by Llama 3)")
                if st.button("Generate Executive Summary"):
                    with st.spinner("Llama 3 is analyzing your performance..."):
                        insights = groq_get_insights(groq_client, metrics)
                        st.markdown(insights)

                st.divider()

                # --- Visuals ---
                st.subheader("Top 10 Products Performance")
                chart_data = df_final.groupby(metrics['p_col'])['_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data, color="#004aad")
                
            else:
                st.error("Could not map the data structure. Please ensure headers are clear.")
    else:
        st.error("Failed to read the file. Please check the format.")
else:
    st.info("Please upload a file to begin.")

