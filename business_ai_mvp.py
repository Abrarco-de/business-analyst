import pandas as pd
import json
import os
import google.generativeai as genai
import streamlit as st

# ================= CONFIG =================

# If running on local, use os.getenv. If Streamlit Cloud, use st.secrets
API_KEY = os.getenv("GEMINI_API_KEY") 

if not API_KEY:
    st.error("❌ API Key not found. Please set GEMINI_API_KEY.")
    st.stop()

genai.configure(api_key=API_KEY)

# Define the model ID as a string, not the object itself yet
MODEL_ID = 'gemini-1.5-flash'

# ================= AI HEADER MAPPING =================

def get_header_mapping(dirty_columns):
    prompt = f"""
    You are a professional data analyst.
    I have a business file with these headers: {dirty_columns}

    Map them to this STANDARD SCHEMA:
    - transaction_id
    - timestamp
    - product_name
    - quantity
    - unit_price
    - cost_price

    Rules:
    1. Return ONLY valid JSON.
    2. Do NOT explain anything.
    3. If a column is missing, do not include it in the JSON.
    Example Output: {{"Item": "product_name", "Qty": "quantity"}}
    """

    # Initialize model correctly using the string ID
    model = genai.GenerativeModel(MODEL_ID)
    response = model.generate_content(prompt)

    text = response.text.strip()
    # Clean AI formatting if present
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception as e:
        st.error(f"AI returned invalid JSON: {text}")
        return {}

# ================= FILE PROCESSING =================

def process_business_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    original_columns = list(df.columns)

    # AI mapping
    mapping = get_header_mapping(original_columns)
    
    if not mapping:
        st.warning("AI could not map any columns. Please check your file headers.")
        return None

    # Rename columns and filter to only those we mapped
    df = df.rename(columns=mapping)
    valid_cols = [c for c in mapping.values() if c in df.columns]
    df = df[valid_cols]

    # Numeric cleaning: Fill empty with 0 so math doesn't break
    for col in ["quantity", "unit_price", "cost_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# ================= INSIGHTS ENGINE =================

def generate_insights(df):
    # Calculations
    # Check if we have the columns needed for profit
    has_prices = "unit_price" in df.columns and "quantity" in df.columns
    has_costs = "cost_price" in df.columns
    
    df["revenue"] = df["unit_price"] * df["quantity"] if has_prices else 0
    df["total_cost"] = df["cost_price"] * df["quantity"] if (has_prices and has_costs) else 0
    df["profit"] = df["revenue"] - df["total_cost"]

    insights = {
        "total_revenue": round(df["revenue"].sum(), 2),
        "total_profit": round(df["profit"].sum(), 2),
    }

    if insights["total_revenue"] > 0:
        insights["profit_margin_percent"] = round(
            (insights["total_profit"] / insights["total_revenue"]) * 100, 2
        )
    else:
        insights["profit_margin_percent"] = 0

    # Top 5 Products by Revenue
    if "product_name" in df.columns:
        insights["top_products"] = df.groupby("product_name")["revenue"].sum().sort_values(ascending=False).head(5).to_dict()
        
        # Loss Makers
        loss_df = df.groupby("product_name")["profit"].sum().sort_values()
        insights["loss_products"] = loss_df[loss_df < 0].head(5).to_dict()
    else:
        insights["top_products"] = {}
        insights["loss_products"] = {}

    return insights

# ================= STREAMLIT UI =================

st.set_page_config(page_title="Saudi Shop Helper", page_icon="🇸🇦")
st.title("🇸🇦 Saudi Shop Helper")
st.write("Upload your POS export to see your true profit.")

file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if file:
    with st.spinner("AI is analyzing your data..."):
        clean_df = process_business_file(file)
        
        if clean_df is not None:
            stats = generate_insights(clean_df)
            
            # Display Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Sales", f"{stats['total_revenue']} SAR")
            col2.metric("Net Profit", f"{stats['total_profit']} SAR")
            col3.metric("Margin", f"{stats['profit_margin_percent']}%")
            
            st.divider()
            
            # Display Charts
            if stats["top_products"]:
                st.subheader("Top Selling Products")
                st.bar_chart(pd.Series(stats["top_products"]))
                
            if stats["loss_products"]:
                st.error("⚠️ Warning: These items are losing you money!")
                st.table(pd.DataFrame(stats["loss_products"].items(), columns=["Product", "Loss (SAR)"]))







