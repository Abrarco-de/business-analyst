import streamlit as st
from business_ai_mvp import *

st.set_page_config(page_title="Dual-AI Business Analyst", layout="wide")

# Secrets Management
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]

client = configure_engines(GEMINI_KEY, OPENAI_KEY)

st.title("🤖 Multi-AI SME Analyst")
st.write("Gemini (Mapping) + Python (Math) + GPT-4o (Strategy)")

file = st.file_uploader("Upload Sales Data", type=["csv"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        # 1. Gemini Architecture Phase
        with st.status("Initializing AI Engines...") as status:
            st.write("Gemini mapping schema...")
            schema = gemini_get_schema(df_raw.columns)
            
            st.write("Python calculating metrics...")
            m, df_final = calculate_precise_metrics(df_raw, schema)
            status.update(label="Analysis Complete!", state="complete")

        # 2. Display Numbers (Python)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"{m['rev']:,.2f} SAR")
        c2.metric("Total Profit", f"{m['prof']:,.2f} SAR")
        c3.metric("ZATCA VAT (15%)", f"{m['vat']:,.2f} SAR")

        st.divider()
        
        # 3. Best Sellers
        w1, w2 = st.columns(2)
        w1.info(f"🏆 **Best Seller:** {m['best_seller']}")
        w2.success(f"💰 **Highest Profit Maker:** {m['most_profitable']}")

        # 4. GPT-4o Strategy Phase
        st.subheader("🚀 GPT-4o Strategic Recommendations")
        if st.button("Generate CEO Strategy"):
            with st.spinner("GPT-4o is thinking..."):
                strategy = gpt_get_strategy(client, m)
                st.markdown(strategy)

        # 5. Chart
        st.subheader("Sales by Category")
        st.bar_chart(df_final.groupby(m['p_col'])['_rev'].sum())


