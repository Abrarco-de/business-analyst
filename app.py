import streamlit as st
import pandas as pd
import google.generativeai as genai
from business_ai_mvp import process_business_file, get_header_mapping, generate_insights, configure_ai

# 1. Page Configuration
st.set_page_config(page_title="Visionary SME Analyst", layout="wide", page_icon="📈")

# 2. Professional UI Styling (Force visibility for metrics)
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1E3A8A !important; 
        border-radius: 12px; 
        padding: 20px; 
        border: 1px solid #2563EB;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricValue"] { color: white !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #CBD5E1 !important; font-size: 1rem !important; }
    .stApp { background-color: #F8FAFC; }
    </style>
    """, unsafe_allow_html=True)

# 3. API Authentication
if "GEMINI_API_KEY" in st.secrets:
    # We pass the key to our config function which forces 'REST' transport
    is_ready = configure_ai(st.secrets["GEMINI_API_KEY"])
else:
    st.sidebar.error("⚠️ API Key missing. Please add GEMINI_API_KEY to Streamlit Secrets.")
    is_ready = False

# 4. Main Interface
st.title("📈 Visionary SME Analyst")
st.markdown("#### Intelligent Business Insights for the Saudi Market")

uploaded_file = st.file_uploader("Upload your sales data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Load and clean the file
    df_raw = process_business_file(uploaded_file)
    
    if df_raw is not None and not df_raw.empty:
        # Step 1: Map headers to standard names
        mapping = get_header_mapping(list(df_raw.columns))
        df_final = df_raw.rename(columns=mapping)
        
        # Step 2: Remove any accidental duplicate columns after renaming
        df_final = df_final.loc[:, ~df_final.columns.duplicated()].copy()
        
        # Step 3: Run the calculation engine
        res = generate_insights(df_final)

        # --- ROW 1: KEY PERFORMANCE INDICATORS ---
        st.subheader("Financial Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Revenue", f"{res['revenue']:,} SAR")
        m2.metric("Estimated Profit", f"{res['profit']:,} SAR", f"{res['margin']}% Margin")
        m3.metric("VAT Liability (15%)", f"{res['vat']:,} SAR")
        m4.metric("Cost Basis", "Estimated" if res['is_estimated'] else "From Data")

        st.divider()

        # --- ROW 2: TOP PERFORMERS ---
        l1, l2 = st.columns(2)
        with l1:
            st.info(f"🏆 **Best Seller (Volume)**\n\n{res['best_seller']}")
        with l2:
            st.success(f"💰 **Top Revenue Contributor**\n\n{res['most_profitable']}")

        st.divider()

        # --- ROW 3: VISUALS & AI STRATEGY ---
        col_chart, col_ai = st.columns([2, 1])
        
        with col_chart:
            st.subheader("Revenue Distribution")
            # Group by the identified product column
            chart_data = res['df'].groupby(res['name_col'])['calc_rev'].sum().sort_values(ascending=False).head(10)
            st.bar_chart(chart_data, color="#1E3A8A")

        with col_ai:
            st.subheader("AI Growth Strategy")
            if st.button("✨ Generate Growth Advice"):
                if not is_ready:
                    st.error("AI is not configured. Check your API key.")
                else:
                    with st.spinner("Consulting Gemini AI..."):
                        # Double Fallback Logic to prevent 404 errors
                        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
                        ai_success = False
                        
                        for m_name in models_to_try:
                            try:
                                model = genai.GenerativeModel(m_name)
                                prompt = f"""
                                Act as a Saudi retail expert. Analyze this data:
                                - Total Revenue: {res['revenue']} SAR
                                - Top Product: {res['best_seller']}
                                - Profit Margin: {res['margin']}%
                                Give 3 high-impact, short tactical tips for growing this business in Saudi Arabia.
                                """
                                response = model.generate_content(prompt)
                                if response.text:
                                    st.markdown("---")
                                    st.markdown(response.text)
                                    ai_success = True
                                    break
                            except Exception:
                                continue # Try the next model version
                        
                        if not ai_success:
                            st.error("The AI service is currently overloaded or restricted in your region.")
                            
        st.balloons()
    else:
        st.error("The uploaded file could not be read. Please ensure it contains data.")

else:
    # Helpful instructions for the user when no file is uploaded
    st.info("👋 Welcome! Please upload a sales report to begin your analysis.")
    st.image("https://img.freepik.com/free-vector/data-analysis-concept-illustration_114360-1611.jpg", width=400)

