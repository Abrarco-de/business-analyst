import pandas as pd
import json
import os
import google.generativeai as genai

# ================= CONFIG =================
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set")

client = genai.Client(api_key=API_KEY)

STANDARD_SCHEMA = {
    "transaction_id",
    "timestamp",
    "product_name",
    "quantity",
    "unit_price",
    "cost_price"
}

# ================= FILE LOADER =================
def load_file(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xml"):
        return pd.read_xml(file)
    else:
        raise ValueError("Unsupported file format")

# ================= AI HEADER MAPPING =================
def get_header_mapping(dirty_columns):
    prompt = f"""
You are a data analyst.

Dirty headers:
{dirty_columns}

Map them to ONLY these fields:
{list(STANDARD_SCHEMA)}

Return ONLY valid JSON.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    try:
        mapping = json.loads(response.text.strip())
    except:
        raise ValueError("AI returned invalid JSON")

    clean_mapping = {
        k: v for k, v in mapping.items()
        if v in STANDARD_SCHEMA
    }

    if not clean_mapping:
        raise ValueError("No valid column mapping found")

    return clean_mapping

# ================= DATA CLEANER =================
def process_business_file(uploaded_file):
    df = load_file(uploaded_file)

    mapping = get_header_mapping(list(df.columns))
    df = df.rename(columns=mapping)

    required = {"product_name", "quantity", "unit_price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in ["quantity", "unit_price", "cost_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# ================= ANALYTICS =================
def generate_insights(df):
    df["revenue"] = df["unit_price"] * df["quantity"]
    df["total_cost"] = df.get("cost_price", 0) * df["quantity"]
    df["profit"] = df["revenue"] - df["total_cost"]

    return {
        "total_revenue": round(df["revenue"].sum(), 2),
        "total_profit": round(df["profit"].sum(), 2),
        "profit_margin": round(
            (df["profit"].sum() / df["revenue"].sum() * 100)
            if df["revenue"].sum() > 0 else 0, 1
        ),
        "top_products": (
            df.groupby("product_name")["revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        ),
        "loss_products": df[df["profit"] < 0]["product_name"].unique().tolist()
    }

