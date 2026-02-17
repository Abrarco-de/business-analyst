import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Profit Intelligence", layout="wide", page_icon="🇸🇦")

# Initialize AI
API_KEY = os.getenv("GEMINI_API_KEY") # Ensure this is in your Secrets
configure_ai(API_KEY)

st.title("🇸🇦 Saudi SME Analyst")
st.markdown("### Transactional Intelligence Dashboard")

file = st.file_uploader("Upload your POS/Retail Export (Excel or CSV)", type=["xlsx", "csv"])

if file:
    with st.spinner("Processing data..."):
        df_raw = process_business_file(file)
        
        if df_raw is not None:
            # 1. Map Headers
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            
            # 2. Analyze
            metrics = generate_insights(df_final)
            
            # 3. Metrics Display
            st.subheader("Financial Key Performance Indicators (KPIs)")
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR")
            
            # Show "Estimated" if we had to guess the cost
            profit_label = "Net Profit" if not metrics['is_estimated_cost'] else "Estimated Profit (65% COGS)"
            c2.metric(profit_label, f"{metrics['total_profit']:,} SAR", delta=f"{metrics['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            c4.metric("Data Rows", len(df_raw))

            st.divider()

            # 4. Visualizations
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Top Products/Categories by Revenue")
                # Calculate revenue per row for the chart
                if "total_amount" in df_final.columns:
                    df_final['chart_rev'] = df_final['total_amount']
                else:
                    df_final['chart_rev'] = df_final.get('unit_price', 0) * df_final.get('quantity', 0)
                
                # Group by Name or Category
                name_col = "product_name" if "product_name" in df_final.columns else df_final.columns[0]
                top_data = df_final.groupby(name_col)['chart_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(top_data)

            with col_right:
                st.subheader("Mapping Verification")
                st.write("The AI identified your columns as follows:")
                st.json(mapping)
                
            st.success("Analysis successful. If the numbers look wrong, check the 'Mapping Verification' above.")








