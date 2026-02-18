import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

st.set_page_config(page_title="Visionary SME Analyst", layout="wide")

# UI STYLING
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 12px; padding: 15px; border: 1px solid #2563EB;
    }
    [data-testid="stMetricValue"] { color: white !important; font-weight: bold !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; }
    </style>
    """, unsafe_allow_html=True)

# API SETUP
if "GEMINI_API_KEY" in st.secrets:
    configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("Add GEMINI_API_KEY to Secrets.")

st.title("📈 Visionary SME Analyst")
file = st.file_uploader("Upload Transaction File", type=["csv", "xlsx"])

if file:
    df_raw = process_business_file(file)
    if not df_raw.empty:
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        res = generate_insights(df_final)

        # 1. METRICS
        st.subheader("Performance Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT (15%)", f"{res['vat']:,} SAR")
        m4.metric("Cost Mode", "Estimated" if res['is_estimated'] else "Actual")

        st.divider()

        # 2. LEADERS
        l1, l2 = st.columns(2)
        l1.info(f"🏆 **Best Seller (Volume):**\n\n{res['best_seller']}")
        l2.success(f"💰 **Top Revenue Source:**\n\n{res['most_profitable']}")

        # 3. CHART & AI
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Sales by Category")
            chart_data = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")
        
    with c2:
            st.subheader("AI Growth Strategy")
            if st.button("✨ Generate Strategy"):
                try:
                    # 'gemini-1.5-flash' is the stable production name. 
                    # If this fails, the system is forced to look for the version available to your key.
                    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                    
                    prompt = f"Analyze Saudi SME: Rev {res['revenue']} SAR, Top Item {res['best_seller']}. Give 3 growth tips."
                    
                    # We add safety settings to ensure the request is standard
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        st.info(response.text)
                    else:
                        st.warning("AI reached a limit. Try again in a moment.")
                        
                except Exception as e:
                    # If gemini-1.5-flash fails, we try the backup 'gemini-pro'
                    try:
                        model = genai.GenerativeModel('gemini-pro')
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except:
                        st.error("Model version mismatch. Please update the 'google-generativeai' library.")
                         st.error("File is empty or corrupted.")





