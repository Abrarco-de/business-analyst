import streamlit as st
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Key missing!")
    ai_status = False

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload Data", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if df_raw is not None:
        mapping = get_header_mapping(list(df_raw.columns))
        df_mapped = df_raw.rename(columns=mapping)
        res = generate_insights(df_mapped)

        # ROW 1: METRICS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Net Profit", f"{res['profit']:,} SAR")
        m3.metric("Margin", f"{res['margin']}%")
        m4.metric("Top Product", res['best_seller'])

        st.divider()

        # ROW 2: CHART & AI
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("Sales Performance")
            if res['revenue'] > 0:
                chart_data = res['df'].groupby(res['name_col'])['temp_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data)
        
        with col_right:
            st.subheader("AI Strategic Advice")
            if st.button("✨ Analyze Business"):
                if res['revenue'] > 0 and ai_status:
                    with st.spinner("Gemini is thinking..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            prompt = f"Business Revenue: {res['revenue']} SAR. Profit: {res['profit']} SAR. Top Product: {res['best_seller']}. Give 3 short, professional growth tips."
                            resp = model.generate_content(prompt)
                            st.info(resp.text)
                        except Exception as e:
                            st.error("AI is overloaded. Please wait 10 seconds and click again.")
                else:
                    st.warning("Please ensure data is loaded correctly (Revenue > 0).")





