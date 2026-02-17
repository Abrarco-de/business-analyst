import pandas as pd
import json
import os
import google.generativeai as genai

# ================= CONFIG =================

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in Streamlit Secrets")

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash-latest"

# ================= AI HEADER MAPPING =================

def get_header_mapping(dirty_columns):
    prompt = f"""
You are a professional data analyst.

I have a business CSV/Excel file with these headers:
{dirty_columns}

Map them to this STANDARD SCHEMA:
- transaction_id
- timestamp
- product_name
- quantity
- unit_price
- cost_price

Rules:
- Return ONLY valid JSON
- Do NOT explain anything
- If a column is missing, ignore it

Example:
{{"Item Name": "product_name"}}
"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)

    text = response.text.strip()

    # Safety cleanup
    text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)

# ================= FILE PROCESSING =================

def process_business_file(uploaded_file):
    # Read file safely
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    original_columns = list(df.columns)

    # AI mapping
    mapping = get_header_mapping(original_columns)

    # Rename columns
    df = df.rename(columns=mapping)

    # Keep only required columns
    required_cols = list(mapping.values())
    df = df[required_cols]

    # Numeric cleaning
    for col in ["quantity", "unit_price", "cost_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# ================= INSIGHTS ENGINE =================

def generate_insights(df):
    df["revenue"] = df["unit_price"] * df["quantity"]
    df["total_cost"] = df["cost_price"] * df["quantity"]
    df["profit"] = df["revenue"] - df["total_cost"]

    insights = {}

    insights["total_revenue"] = round(df["revenue"].sum(), 2)
    insights["total_profit"] = round(df["profit"].sum(), 2)

    if insights["total_revenue"] > 0:
        insights["profit_margin_percent"] = round(
            (insights["total_profit"] / insights["total_revenue"]) * 100, 2
        )
    else:
        insights["profit_margin_percent"] = 0

    top_products = (
        df.groupby("product_name")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    loss_products = (
        df.groupby("product_name")["profit"]
        .sum()
        .sort_values()
        .head(5)
    )

    insights["top_products"] = top_products.to_dict()
    insights["loss_products"] = loss_products[loss_products < 0].to_dict()

    return insights



