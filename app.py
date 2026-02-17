import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Saudi SME Intelligence", layout="wide", page_icon="📈")

# AI Key
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 Business Analyst Pro")
st.markdown("### Advanced Commercial Insights")

file = st.file_uploader("Upload POS Data", type=["xlsx", "csv"])

if file:
    with st.spinner("Calculating Business Metrics..."):
        df_raw = process_business_file(file)
        if df_raw is not None:
            mapping = get_header_mapping(list(df_raw.columns))
            df = df_raw.rename(columns=mapping)
            metrics = generate_insights(df)

            # --- Row 1: Financial KPIs ---
            st.subheader("Financial Health")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue", f"{metrics['total_revenue']:,} SAR", f"{metrics['growth_pct']}% Growth")
            
            profit_label = "Net Profit (Est.)" if metrics['is_estimated_cost'] else "Net Profit"
            c2.metric(profit_label, f"{metrics['total_profit']:,} SAR", f"{metrics['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{metrics['vat_due']:,} SAR")
            c4.metric("Avg. Sale Value", f"{metrics['avg_transaction']:,} SAR")

            st.divider()

            # --- Row 2: Product Performance ---
            st.subheader("Product & Operational Insights")
            p1, p2, p3 = st.columns(3)
            
            with p1:
                st.info(f"**Highest Revenue Product**\n\n### {metrics['top_product_rev']}")
            with p2:
                st.success(f"**Highest Selling (Qty)**\n\n### {metrics['top_product_qty']}")
            with p3:
                # Identify busiest day if date exists
                if 'date' in df.columns and not df['date'].isnull().all():
                    busiest_day = df['date'].dt.day_name().mode()[0]
                    st.warning(f"**Busiest Day of Week**\n\n### {busiest_day}")
                else:
                    st.warning("**Busiest Day**\n\n### No Date Found")

            # --- Row 3: Charts ---
            st.divider()
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.write("### Sales Distribution")
                # Group by Category if available, otherwise Product
                group_col = 'category' if 'category' in df.columns else ('product_name' if 'product_name' in df.columns else df.columns[0])
                chart_data = df.groupby(group_col)['calc_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)

            with col_right:
                st.write("### AI Strategic Advice")
                if st.button("Generate Strategy"):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"Business has {metrics['margin']}% margin and {metrics['growth_pct']}% growth. Top product is {metrics['top_product_rev']}. Give 2 tips for a Saudi SME owner."
                    response = model.generate_content(prompt)
                    st.write(response.text)




