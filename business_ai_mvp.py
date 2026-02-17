import streamlit as st
import pandas as pd
import json
import os
import re
import google.generativeai as genai

# ================= CONFIG =================
# Using Gemini 3 Flash (Latest Feb 2026 version)
MODEL_ID = 'gemini-3-flash-preview' 

# Set your API Key here or in Streamlit Secrets
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("🔑 API Key Missing! Please set GEMINI_API_KEY in your environment.")
    st.stop()

genai.configure(api_key=API_KEY)

# ================= AI ENGINE =================

def get_header_mapping(columns):
    """Uses AI to map messy Saudi POS headers to our standard schema"""
    prompt = f"""
    You are a Saudi Business Analyst. Map these headers: {columns}
    to: [transaction_id, timestamp, product_name, quantity, unit_price, cost_price].
    
    Rules:
    - Match Arabic names (e.g., 'السعر' to unit_price).
    - Return ONLY valid JSON.
    - Example: {{"اسم": "product_name", "الكمية": "quantity"}}
    """
    try:
        model = genai.GenerativeModel(MODEL_ID)
        response = model.generate_content(prompt)
        clean_json = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json)
    except Exception as e:
        st.warning(f"AI Mapping failed, using manual fallback. Error: {e}")
        return {}

def clean_currency_string(value):
    """Removes 'SAR', commas, and spaces so math works"""
    if isinstance(value, str):
        # Removes everything except numbers and decimals
        clean_val = re.sub(r'[^\d.]', '', value)
        return float(clean_val) if clean_val else 0.0
    return value

# ================= CORE LOGIC =================

def process_and_analyze(file):
    # 1. Load File
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    
    # 2. Map Headers
    mapping = get_header_mapping(list(df.columns))
    df = df.rename(columns=mapping)

    # 3. Clean Data (Fixes the '0' profit issue)
    numeric_cols = ["quantity", "unit_price", "cost_price"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_currency_string)
        else:
            df[col] = 0.0 # Create missing columns as 0

    # 4. Smart "Cost Guess" (If shop owner didn't provide cost_price)
    if df["cost_price"].sum() == 0:
        st.info("💡 Note: No cost price found. Estimating profit at 30% margin.")
        df["cost_price"] = df["unit_price"] * 0.7

    # 5. Math
    df["revenue"] = df["unit_price"] * df["quantity"]
    df["total_cost"] = df["cost_price"] * df["quantity"]
    df["profit"] = df["revenue"] - df["total_cost"]

    return df

# ================= STREAMLIT UI =================

st.set_page_config(page_title="Saudi SME Profit AI", layout="wide")
st.title("🇸🇦 SME Profit Dashboard (MVP)")
st.write("Clean your POS data and see true profit for 69 SAR/mo.")

uploaded_file = st.file_uploader("Upload POS Export (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("AI is cleaning and calculating..."):
        data = process_and_analyze(uploaded_file)
        
        # Dashboard Metrics
        rev = data["revenue"].sum()
        prof = data["profit"].sum()
        margin = (prof / rev * 100) if rev > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"{rev:,.2f} SAR")
        c2.metric("Total Profit", f"{prof:,.2f} SAR")
        c3.metric("Net Margin", f"{margin:.1f}%")

        st.divider()

        # Visuals
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Top Products (Revenue)")
            top_rev = data.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(10)
            st.bar_chart(top_rev)

        with col_b:
            st.subheader("Loss-Making Items")
            losses = data.groupby("product_name")["profit"].sum().sort_values()
            loss_items = losses[losses < 0]
            if not loss_items.empty:
                st.dataframe(loss_items, use_container_width=True)
            else:
                st.success("🎉 No loss-making products detected!")

        st.subheader("Cleaned Data Preview")
        st.dataframe(data.head(20), use_container_width=True)





