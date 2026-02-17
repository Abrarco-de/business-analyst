import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import re

# ================= 1. SETUP & CONFIG =================
st.set_page_config(page_title="Saudi SME Analyst", page_icon="🇸🇦", layout="wide")

# Replace with your actual key or use Streamlit Secrets
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("🔑 API Key Missing! Please add your GEMINI_API_KEY.")
    st.stop()

# ================= 2. DATA CLEANING ENGINE =================

def clean_numeric_value(val):
    """Removes 'SAR', commas, and text so Python can do math."""
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    # Remove everything except numbers and decimals
    clean = re.sub(r'[^\d.]', '', str(val))
    return float(clean) if clean else 0.0

def process_file(uploaded_file):
    """Reads CSV/Excel and cleans the hidden junk."""
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        # Clean all potential number columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amt', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        st.error(f"❌ File Error: {e}")
        return None

# ================= 3. AI MAPPING & INSIGHTS =================

def get_ai_mapping(columns):
    """Maps messy headers to standard names using Gemini 2.0."""
    prompt = f"""
    Map these headers: {columns} 
    to exactly: [transaction_id, timestamp, product_name, quantity, unit_price, cost_price].
    Return ONLY valid JSON. Arabic is okay.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    try:
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except:
        return {}

def generate_insights(df):
    """Calculates KPIs with safety fallbacks to prevent KeyErrors."""
    # Ensure columns exist even if AI mapping failed
    rev = df.get("unit_price", 0) * df.get("quantity", 0)
    cost = df.get("cost_price", 0) * df.get("quantity", 0)
    
    total_rev = rev.sum()
    total_prof = (rev - cost).sum()
    
    # SAFETY: Always define the key to prevent KeyError
    insights = {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "profit_margin_percent": 0.0  # Default value
    }
    
    if total_rev > 0:
        insights["profit_margin_percent"] = round((total_prof / total_rev) * 100, 2)
        
    return insights

# ================= 4. DASHBOARD UI =================

st.title("🇸🇦 Saudi SME Profit AI")
st.write("Clean your POS data for 69 SAR/month.")

file = st.file_uploader("Upload your POS Export", type=["csv", "xlsx"])

if file:
    with st.spinner("AI is analyzing..."):
        raw_df = process_file(file)
        if raw_df is not None:
            # 1. AI Rename
            mapping = get_ai_mapping(list(raw_df.columns))
            df = raw_df.rename(columns=mapping)
            
            # 2. Get Insights
            results = generate_insights(df)
            
            # 3. Display Metrics (Using .get() for double safety)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Sales", f"{results.get('total_revenue', 0):,.2f} SAR")
            c2.metric("Net Profit", f"{results.get('total_profit', 0):,.2f} SAR")
            c3.metric("Margin (%)", f"{results.get('profit_margin_percent', 0)}%")
            
            st.divider()
            st.subheader("Data Preview")
            st.dataframe(df.head(10), use_container_width=True)








