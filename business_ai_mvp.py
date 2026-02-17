import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import re

# ================= 1. CONFIG =================
# Use the latest stable 2026 model
MODEL_ID = 'gemini-2.0-flash' 
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("🔑 API Key Missing")

# ================= 2. THE "MISSING" FUNCTIONS =================

def process_business_file(uploaded_file):
    """Reads the file and cleans currency/symbols."""
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Strip currency symbols (SAR, $, ,) from all columns
        def clean_num(x):
            if isinstance(x, str):
                res = re.sub(r'[^\d.]', '', x)
                return float(res) if res else 0.0
            return x
        
        # We clean potential numeric columns early
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amt']):
                df[col] = df[col].apply(clean_num)
        return df
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def get_header_mapping(columns):
    """AI maps headers to our schema."""
    prompt = f"Map these headers: {columns} to [transaction_id, timestamp, product_name, quantity, unit_price, cost_price]. Return ONLY JSON."
    model = genai.GenerativeModel(MODEL_ID)
    response = model.generate_content(prompt)
    clean_json = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(clean_json)

def generate_insights(df):
    """Calculates Revenue, Profit, and Losses."""
    # Logic to ensure math works even if columns are missing
    df["revenue"] = df.get("unit_price", 0) * df.get("quantity", 0)
    df["total_cost"] = df.get("cost_price", 0) * df.get("quantity", 0)
    df["profit"] = df["revenue"] - df["total_cost"]

    insights = {
        "total_revenue": round(df["revenue"].sum(), 2),
        "total_profit": round(df["profit"].sum(), 2),
        "top_products": df.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(5).to_dict() if "product_name" in df.columns else {}
    }
    return insights

# ================= 3. THE UI SECTION =================

st.title("🇸🇦 Saudi SME Analyst")

uploaded_file = st.file_uploader("Upload POS Data", type=["csv", "xlsx"])

if uploaded_file:
    # Use the functions we just defined above
    df = process_business_file(uploaded_file)
    
    if df is not None:
        # AI Mapping
        mapping = get_header_mapping(list(df.columns))
        df = df.rename(columns=mapping)
        
        # Analytics
        stats = generate_insights(df)
        
        # Display Results
        c1, c2 = st.columns(2)
        c1.metric("Total Sales", f"{stats['total_revenue']} SAR")
        c2.metric("Total Profit", f"{stats['total_profit']} SAR")
        
        if stats["top_products"]:
            st.write("### Top Products")
            st.bar_chart(pd.Series(stats["top_products"]))





