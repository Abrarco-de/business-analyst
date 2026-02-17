import streamlit as st
import os
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai
import google.generativeai as genai

st.set_page_config(page_title="Saudi SME Analyst", layout="wide", page_icon="🇸🇦")

# Setup
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Business Intelligence MVP")
st.markdown("### Advanced Profit & Sales Analytics")

file = st.file_uploader("Upload POS Data", type=["xlsx", "csv"])

if file:
    with st.spinner("Analyzing..."):
        df_raw = process_business_file(file)
        if df_raw is not None:
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            metrics = generate_insights(df_final)
            
            # --- FEATURE 1: KPI CARDS ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR")
            c2.metric("Profit", f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}% Margin")
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            c4.metric("Estimated Cost", "65%" if metrics['is_estimated_cost'] else "Actual")

            st.divider()

            # --- FEATURE 2: VISUAL CHARTS ---
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Top Sales by Product/Category")
                # Calculate row-level revenue for the chart
                if "total_amount" in df_final.columns:
                    df_final['row_rev'] = df_final['total_amount']
                else:
                    df_final['row_rev'] = df_final.get('unit_price', 0) * df_final.get('quantity', 0)
                
                name_col = "product_name" if "product_name" in df_final.columns else df_final.columns[0]
                chart_data = df_final.groupby(name_col)['row_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

            with col_b:
                st.subheader("Mapping Intelligence")
                st.info("How the AI understood your file columns:")
                st.write(mapping)

            # --- FEATURE 3: AI BUSINESS STRATEGY ---
            st.divider()
            if st.button("Get AI Growth Advice"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"A Saudi shop has {metrics['total_revenue']} SAR revenue and {metrics['margin']}% profit margin. Give 3 quick tips to grow."
                response = model.generate_content(prompt)
                st.light_bulb = st.info(response.text)
