import streamlit as st
import os
import pandas as pd
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Saudi SME Intelligence", layout="wide", page_icon="🇸🇦")

# Initialize
API_KEY = os.getenv("GEMINI_API_KEY")
configure_ai(API_KEY)

st.title("🇸🇦 SME Profit Intelligence")
st.caption("Advanced Retail Analytics for Saudi Businesses")

uploaded_file = st.file_uploader("Upload POS CSV/Excel", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("Processing Business Data..."):
        df_raw = process_business_file(uploaded_file)
        
        if df_raw is not None:
            mapping = get_header_mapping(list(df_raw.columns))
            df_final = df_raw.rename(columns=mapping)
            results = generate_insights(df_final)

            # --- KPI SECTION ---
            st.subheader("Financial Performance")
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("Total Revenue", f"{results['revenue']:,} SAR")
            
            p_label = "Net Profit (Est.)" if results['is_estimated'] else "Net Profit"
            c2.metric(p_label, f"{results['profit']:,} SAR", f"{results['margin']}% Margin")
            
            c3.metric("ZATCA VAT (15%)", f"{results['vat']:,} SAR")
            c4.metric("Transactions", len(df_raw))

            st.divider()

            # --- ANALYTICS SECTION ---
            col_left, col_right = st.columns([2, 1])

            with col_left:
                st.subheader("Top Revenue Contributors")
                # Prepare chart data
                df_c = results['raw_data']
                name_col = "product_name" if "product_name" in df_c.columns else df_c.columns[0]
                
                if "total_amount" in df_c.columns:
                    rev_series = df_c["total_amount"]
                else:
                    rev_series = pd.to_numeric(df_c.get("unit_price", 0)) * pd.to_numeric(df_c.get("quantity", 0))
                
                chart_df = pd.DataFrame({ 'Item': df_c[name_col], 'Revenue': rev_series })
                top_10 = chart_df.groupby('Item')['Revenue'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(top_10)

            with col_right:
                st.subheader("Intelligence Log")
                st.info(f"AI mapped {len(mapping)} columns successfully.")
                with st.expander("See column mapping"):
                    st.json(mapping)
                
                if results['margin'] < 20:
                    st.warning("⚠️ Low Margin Alert: Your profit margin is below 20%. Consider reviewing your costs.")
                else:
                    st.success("✅ Healthy Margins: Your business is performing well.")

            st.success("Analysis ready for review.")
        else:
            st.error("Could not read file. Please ensure it's a valid CSV or Excel.")

