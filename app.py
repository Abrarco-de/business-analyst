import streamlit as st
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

# Set UI Theme
st.set_page_config(page_title="SME Analyst Pro", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #1E3A8A !important; border-radius: 10px; padding: 20px; border: 1px solid #2563EB; }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# API Configuration
if "GEMINI_API_KEY" in st.secrets:
    ai_status = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Missing GEMINI_API_KEY in Secrets.")
    ai_status = False

st.title("📈 Visionary SME Analyst")
st.write("Professional Business Intelligence & AI Strategy")

uploaded_file = st.file_uploader("Upload your sales report (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    df_raw = process_business_file(uploaded_file)
    
    if df_raw is not None and not df_raw.empty:
        # Step 1: Logic Mapping
        mapping = get_header_mapping(list(df_raw.columns))
        df_mapped = df_raw.rename(columns=mapping)
        
        # Step 2: Accurate Calculations
        res = generate_insights(df_mapped)

        # Step 3: Performance Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT (15%)", f"{res['vat']:,} SAR")
        m4.metric("Cost Mode", "Estimate" if res['is_estimated'] else "Verified")

        st.divider()

        # Step 4: Charts and AI Tips
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.subheader("Sales by Category")
            # Safety check for columns before charting
            if not res['df'].empty and 'temp_rev' in res['df'].columns:
                target = res['name_col']
                chart_data = res['df'].groupby(target)['temp_rev'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(chart_data, color="#1E3A8A")
                st.info(f"🏆 Best Seller: {res['best_seller']}")
            else:
                st.warning("No numeric data found for charts.")

        with c_right:
            st.subheader("AI Growth Consultant")
            if st.button("✨ Generate AI Tips"):
                if ai_status:
                    with st.spinner("Consulting Gemini..."):
                        # Fallback for models to avoid 404s
                        success = False
                        for m_name in ['gemini-1.5-flash', 'gemini-pro']:
                            try:
                                model = genai.GenerativeModel(m_name)
                                p = f"Revenue: {res['revenue']} SAR, Top Item: {res['best_seller']}. Give 3 short tactical growth tips."
                                response = model.generate_content(p)
                                if response.text:
                                    st.success(response.text)
                                    success = True
                                    break
                            except:
                                continue
                        if not success:
                            st.error("AI service busy. Your financial data is still accurate above.")
                else:
                    st.error("AI Key not configured properly.")
    else:
        st.error("File is empty or could not be processed.")
        



