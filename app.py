import streamlit as st
import pandas as pd
from business_ai_mvp import configure_engines, calculate_precise_metrics, groq_get_insights

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

# Initialize
groq_client = configure_engines(GEMINI_KEY, GROQ_KEY)

st.title("📈 Visionary SME Analyst")

uploaded_file = st.file_uploader("Upload Sales Data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Use pandas to read the file first
    try:
        df_input = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Calculate
        with st.spinner("Analyzing data with Advanced Metrics..."):
            m, df_final = calculate_precise_metrics(df_input)
        
        # Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"{m['rev']:,} SAR")
        c2.metric("Total Profit", f"{m['prof']:,} SAR")
        c3.metric("ZATCA VAT (15%)", f"{m['vat']:,} SAR")

        st.divider()
        
        w1, w2 = st.columns(2)
        w1.info(f"🏆 **Best Seller:** {m['best_seller']}")
        w2.success(f"💰 **Highest Profit Maker:** {m['top_profit_prod']}")

        st.divider()
        
        if st.button("Generate AI Growth Strategy"):
            with st.spinner("Llama 3 is analyzing..."):
                advice = groq_get_insights(groq_client, m)
                st.markdown(advice)
                
        st.bar_chart(df_final.groupby(m['p_col'])['_rev'].sum().sort_values(ascending=False).head(10))

    except Exception as e:
        st.error(f"Error processing file: {e}")
