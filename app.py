import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Pro Intelligence", layout="wide", page_icon="📈")

# API Key
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Saudi SME Analyst Pro")
st.markdown("### Decision-Ready Business Intelligence")

file = st.file_uploader("Upload POS Data (CSV/Excel)", type=["xlsx", "csv"])

if file:
    with st.spinner("AI analyzing your business performance..."):
        df_raw = process_business_file(file)
        if df_raw is not None:
            mapping = get_header_mapping(list(df_raw.columns))
            df = df_raw.rename(columns=mapping)
            metrics = generate_insights(df)

            # --- Financial KPIs ---
            st.subheader("Financial Snapshot")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR", f"{metrics['growth_pct']}% Growth")
            
            prof_label = "Net Profit (Est.)" if metrics['is_estimated_cost'] else "Net Profit"
            c2.metric(prof_label, f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            c4.metric("Avg. Sale Value", f"{metrics['avg_transaction']:,} SAR")

            st.divider()

            # --- Pro Insights Section ---
            st.subheader("🏆 Winning Products")
            p1, p2, p3 = st.columns(3)
            
            with p1:
                st.info(f"**Highest Revenue Product**\n\n### {metrics['top_product_rev']}")
                st.caption("This item brings in the most money.")
            with p2:
                st.success(f"**Highest Selling (Qty)**\n\n### {metrics['top_product_qty']}")
                st.caption("This is your most popular item by volume.")
            with p3:
                st.warning(f"**Highest Return (Profit)**\n\n### {metrics['top_product_profit']}")
                st.caption("This item is your best 'Money Maker'.")

            # --- Charts & Analysis ---
            st.divider()
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.write("### Sales by Product (Top 10)")
                prod_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
                chart_data = df.groupby(prod_col)['calc_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

            with col_right:
                st.write("### AI Executive Summary")
                if st.button("Generate Strategy"):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Business Revenue: {metrics['total_revenue']} SAR, Margin: {metrics['margin']}%, Best Product: {metrics['top_product_profit']}. Provide 3 short executive tips for a Saudi SME owner."
                    response = model.generate_content(prompt)
                    st.write(response.text)


