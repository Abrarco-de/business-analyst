import streamlit as st
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="SME Analyst Pro", layout="wide")

# 1. UI Styling
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E3A8A !important; border-radius: 10px; padding: 15px; }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Setup AI
if "GEMINI_API_KEY" in st.secrets:
    ai_ready = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.warning("Add GEMINI_API_KEY to Secrets.")
    ai_ready = False

st.title("📈 Visionary SME Analyst")

file = st.file_uploader("Upload Data", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    
    if df_raw is not None and not df_raw.empty:
        # Step 1: Logic-based Mapping
        mapping = get_header_mapping(list(df_raw.columns))
        df_mapped = df_raw.rename(columns=mapping)
        
        # Step 2: Python-based Math
        res = generate_insights(df_mapped)

        # Step 3: Display Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Revenue", f"{res['revenue']:,} SAR")
        col2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        col3.metric("VAT Liability", f"{res['vat']:,} SAR")
        col4.metric("Calculation", "Market Estimate" if res['is_estimated'] else "Verified Data")

        st.divider()

        # Step 4: Charts and AI Tips
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.subheader("Top Revenue Categories")
            if not res['df'].empty:
                chart_data = res['df'].groupby(res['name_col'])['temp_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data, color="#1E3A8A")
            else:
                st.info("Upload data to see the chart.")

        with c_right:
            st.subheader("AI Consultant")
            if st.button("✨ Get Business Strategy"):
                if ai_ready:
                    with st.spinner("Consulting AI..."):
                        # Model fallback to prevent 404
                        for m_name in ['gemini-1.5-flash', 'gemini-pro']:
                            try:
                                model = genai.GenerativeModel(m_name)
                                p = f"Revenue: {res['revenue']} SAR. Top Item: {res['best_seller']}. Give 3 growth tips."
                                response = model.generate_content(p)
                                st.success(response.text)
                                break
                            except Exception:
                                continue
                else:
                    st.error("AI connection not available.")
    else:
        st.error("Please upload a valid file.")



