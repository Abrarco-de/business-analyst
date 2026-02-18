import pandas as pd
from typing import Dict
import re

# Optional AI
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

_model = None

def configure_ai(api_key):
    global _model
    if api_key and AI_AVAILABLE:
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-pro")
    else:
        _model = None


# ALIASES for schema detection
COLUMN_ALIASES = {
    "product_name": ["product","item","menu","name","description","prod"],
    "quantity": ["qty","quantity","units","sold","count"],
    "price": ["price","unit_price","rate","sell_price"],
    "sales": ["sales","revenue","total"],
    "cost": ["cost","cost_price","purchase","buy_price"],
    "profit": ["profit","profit_value"],
    "discount": ["discount","disc","rebate"]
}

def find_best_column(df_cols, aliases):
    df_lc = [c.lower().strip() for c in df_cols]
    for alias in aliases:
        if alias in df_lc:
            return df_cols[df_lc.index(alias)]
    return None

def map_schema(df: pd.DataFrame) -> Dict[str,str]:
    # rule-based mapping
    schema = {}
    for standard, aliases in COLUMN_ALIASES.items():
        matched = find_best_column(df.columns, aliases)
        if matched:
            schema[matched] = standard

    return schema

def validate_schema(mapped_fields):
    # must have revenue or (quantity + price)
    if "sales" in mapped_fields.values():
        return True
    if "quantity" in mapped_fields.values() and "price" in mapped_fields.values():
        return True
    raise ValueError("Data must contain either sales OR (quantity + price) columns.")

def process_business_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df.columns = [c.lower().strip() for c in df.columns]
    schema = map_schema(df)

    validate_schema(schema)

    # rename for internal use
    df = df.rename(columns=schema)

    # numeric conversion
    for col in ["quantity","price","sales","cost","profit","discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ensure default fields
    if "product_name" not in df:
        df["product_name"] = "Unknown"

    if "sales" not in df and "price" in df and "quantity" in df:
        df["sales"] = df["price"] * df["quantity"]

    if "profit" not in df:
        df["profit"] = df["sales"] - df.get("cost",0)

    return df

def calculate_metrics(df: pd.DataFrame) -> Dict:
    metrics = {}

    # total metrics
    metrics["total_revenue"] = round(df["sales"].sum(),2)
    metrics["total_profit"] = round(df["profit"].sum(),2)
    metrics["gross_margin_pct"] = round(
        (metrics["total_profit"]/metrics["total_revenue"]*100) if metrics["total_revenue"] else 0,2
    )
    metrics["vat_due"] = round(metrics["total_revenue"] * 0.15,2)

    # average indicators
    metrics["average_transaction_value"] = round(
        metrics["total_revenue"] / max(len(df),1),2
    )

    # product-level analysis
    grp = df.groupby("product_name").agg({
        "sales":"sum", "profit":"sum", "quantity":"sum"
    }).reset_index()

    grp["margin_pct"] = (
        grp["profit"] / grp["sales"] * 100
    ).replace([float("inf"),-float("inf")],0).fillna(0)

    metrics["top_revenue_products"] = (
        grp.sort_values("sales",ascending=False)
        .head(5)[["product_name","sales"]]
        .to_dict("records")
    )
    metrics["top_profit_products"] = (
        grp.sort_values("profit",ascending=False)
        .head(5)[["product_name","profit"]]
        .to_dict("records")
    )
    metrics["loss_making_products"] = (
        grp[grp["profit"] < 0]
        .sort_values("profit")[["product_name","profit"]]
        .to_dict("records")
    )
    metrics["high_volume_low_margin"] = (
        grp[
            (grp["quantity"] > grp["quantity"].median()) &
            (grp["margin_pct"] < grp["margin_pct"].median())
        ][["product_name","quantity","margin_pct"]]
        .to_dict("records")
    )

    # optional discount summary
    if "discount" in df.columns:
        metrics["total_discount"] = round(df["discount"].sum(),2)
        metrics["discount_rate_pct"] = round(
            (metrics["total_discount"]/metrics["total_revenue"]*100) if metrics["total_revenue"] else 0,2
        )

    return metrics

def generate_ai_insights(metrics: Dict) -> str:
    if _model is None:
        return "AI insights are unavailable because API key is not configured."

    # prepare narrative
    prompt = f"""
You are a senior business analyst specializing in SME retail/cafe/restaurant.
Interpret the following metrics and write a human-readable summary
with practical advice for the business owner:

{metrics}

Respond with:
- High-level summary
- Key strengths
- Key weaknesses
- Practical suggestions
"""
    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI insight generation failed: {e}"








