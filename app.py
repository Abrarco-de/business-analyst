import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Pro Analyst", layout="wide", page_icon="🇸🇦")

# Setup AI Key - Replace with your actual key or use environment variables
API_KEY = "YOUR_GEMINI_API_KEY_HERE" 
configure_ai(API_KEY)

st.title("🇸🇦 Saudi SME Analyst Pro")
st.markdown("### Transactional Business Intelligence Dashboard")

uploaded_file = st.file_uploader("Upload your Business Export (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("AI is processing your financial data..."):
        df_raw = process_business_file(uploaded_file)
        
        if df_raw is not None:
            # 1. AI Mapping
            mapping = get_header_mapping(list(df_raw.columns))
            df = df_raw.rename(columns=mapping)
            
            # 2. Financial Logic
            metrics = generate_insights(df)
            
            # 3. Top KPI Row
            st.subheader("Financial Performance")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR", f"{metrics['growth_pct']}% Growth")
            
            prof_label = "Net Profit (Est. 65% COGS)" if metrics['is_estimated_cost'] else "Net Profit"
            c2.metric(prof_label, f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            c4.metric("Avg. Order Value", f"{metrics['avg_transaction']:,} SAR")
            
            st.divider()
            
            # 4. Product Insights Row
            st.subheader("🏆 Product Excellence")
            p1, p2, p3 = st.columns(3)
            with p1:
                st.info(f"**Highest Revenue Product**\n\n### {metrics['top_product_rev']}")
            with p2:
                st.warning(f"**Best Margin (Highest Profit)**\n\n### {metrics['top_product_profit']}")
            with p3:
                # Busiest Day Logic
                if 'date' in df.columns and not df['date'].isnull().all():
                    busiest = df['date'].dt.day_name().mode()[0]
                    st.success(f"**Busiest Day of Week**\n\n### {busiest}")
                else:
                    st.success("**Busiest Day**\n\n### Date not found")

            # 5. Data Visualization
            st.divider()
            col_chart, col_ai = st.columns([2, 1])
            
            with col_chart:
                st.write("### Revenue by Product (Top 10)")
                prod_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
                chart_data = df.groupby(prod_col)['calc_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)
                
            with col_ai:
                st.write("### AI Strategic Advice")
                if st.button("Generate Recommendations"):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"SME in Saudi with {metrics['margin']}% margin. Best product: {metrics['top_product_profit']}. Give 3 growth tips."
                    response = model.generate_content(prompt)
                    st.write(response.text)
        else:
            st.error("Error reading file. Please ensure it is a valid CSV or Excel file.")

