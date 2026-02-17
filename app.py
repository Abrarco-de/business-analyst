import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Saudi SME Intelligence", layout="wide")

# API Key Setup
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Business Analyst MVP")
st.write("Professional Insights for Saudi SMEs")

file = st.file_uploader("Upload POS Data (Excel/CSV)", type=["xlsx", "csv"])

if file:
    with st.spinner("Analyzing business health..."):
        # 1. Process
        raw_df = process_business_file(file)
        mapping = get_header_mapping(list(raw_df.columns))
        df = raw_df.rename(columns=mapping)
        
        # 2. Analyze
        metrics = generate_insights(df)
        
        # 3. KPI Dashboard
        st.subheader("Financial Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR")
        c2.metric("Net Profit", f"{metrics['total_profit']:,} SAR", delta=f"{metrics['margin']}% Margin")
        c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
        c4.metric("Avg. Basket Size", f"{metrics['atv']:,} SAR")

        st.divider()
        
        # 4. Product Insights
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("### Top Products by Revenue")
            df['rev'] = df.get('unit_price', 0) * df.get('quantity', 0)
            chart_data = df.groupby('product_name')['rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data)
            
        with col_b:
            st.write("### Data Integrity Check")
            st.write("How we mapped your columns:")
            st.json(mapping)

        # 5. Business Advice (AI Powered)
        if st.button("Generate AI Growth Strategy"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            advice_prompt = f"Business has {metrics['margin']}% margin and {metrics['atv']} SAR average sale. Give 3 tips to increase profit in Saudi market. Keep it short."
            advice = model.generate_content(advice_prompt)
            st.info(advice.text)







