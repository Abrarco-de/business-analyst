import pandas as pd
import json
import os
from typing import Dict, List, Optional

# ================= AI CONFIG =================
try:
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

_model = None

def configure_ai(api_key: Optional[str]):
    global _model
    if api_key and AI_AVAILABLE:
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-1.0-pro")
    else:
        _model = None


# ================= STANDARD CONCEPTS =================
STANDARD_FIELDS = {
    "product_name": ["product", "item", "menu", "name", "item_name", "description"],
    "quantity": ["qty", "quantity", "count", "units", "sold"],
    "price": ["price", "unit_price", "selling_price"],
    "sales": ["sales", "revenue", "amount", "total"],
    "cost": ["cost", "purchase", "buying_price"],
    "profit": ["profit", "margin"],
    "discount": ["discount", "disc"]
}

REQUIRED_LOGIC = [
    {"quantity", "price"},
    {"quantity", "sales"},
    {"sales"}  # fallback if only sales exists
]

# ================= FALLBACK RULE ENGINE =================
def rule_based_mapping(columns: List[str]) -> Dict[str, str]:
    mapping = {}
    cols_lower = {c.lower(): c for c in columns}

    for std_field, keywords in STANDARD_FIELDS.items():
        for col_l, col in cols_lower.items():
            if any(k in col_l for k in keywords):
                mapping[col] = std_field
                break

    return mapping


# ================= AI SCHEMA PROPOSAL =================
def ai_schema_mapping(columns: List[str]) -> Dict[str, str]:
    if _model is None:
        return {}

    prompt = f"""
You are a senior data analyst.

Map these columns to business concepts.

Columns:
{columns}

Concepts:
product_name, quantity, price, sales, cost, profit, discount

Rules:
- If unsure, skip the column
- Return JSON only
"""

    try:
        response = _model.generate_content(prompt)
        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception:
        return {}


# ================= VALIDATION ENGINE =================
def validate_schema(mapped_values: set) -> bool:
    for rule in REQUIRED_LOGIC:
        if rule.issubset(mapped_values):
            return True
    return False


# ================= FINAL SCHEMA BUILDER =================
def build_schema(columns: List[str]) -> Dict[str, str]:
    # 1️⃣ AI proposal
    ai_map = ai_schema_mapping(columns)

    # 2️⃣ Rule-based fallback
    rule_map = rule_based_mapping(columns)

    # 3️⃣ Merge (AI wins, rules fill gaps)
    final_map = rule_map.copy()
    final_map.update(ai_map)

    mapped_values = set(final_map.values())

    if not validate_schema(mapped_values):
        raise ValueError(
            "Dataset must contain at least:\n"
            "- quantity + price OR\n"
            "- quantity + sales OR\n"
            "- sales\n"
        )

    return final_map


# ================= FILE PROCESSOR =================
def process_business_file(file) -> pd.DataFrame:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    schema = build_schema(list(df.columns))
    df = df.rename(columns=schema)

    # Ensure numeric columns
    for col in ["quantity", "price", "sales", "cost", "profit", "discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# ================= INSIGHTS ENGINE (NO AI) =================
def generate_insights(df: pd.DataFrame) -> Dict:
    insights = {}

    if "sales" not in df.columns:
        df["sales"] = df.get("quantity", 1) * df.get("price", 0)

    if "profit" not in df.columns:
        cost = df.get("cost", 0)
        df["profit"] = df["sales"] - (df.get("quantity", 1) * cost)

    insights["total_revenue"] = round(df["sales"].sum(), 2)
    insights["total_profit"] = round(df["profit"].sum(), 2)
    insights["margin"] = round(
        (insights["total_profit"] / insights["total_revenue"] * 100)
        if insights["total_revenue"] > 0 else 0,
        2
    )

    if "product_name" in df.columns:
        insights["top_items"] = (
            df.groupby("product_name")["sales"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        )

    insights["vat_due"] = round(insights["total_revenue"] * 0.15, 2)

    return insights
    # ================= ADVANCED METRICS ENGINE =================
def calculate_metrics(df: pd.DataFrame) -> Dict:
    metrics = {}

    # --- Ensure required computed columns ---
    if "sales" not in df.columns:
        df["sales"] = df.get("quantity", 1) * df.get("price", 0)

    if "profit" not in df.columns:
        cost = df.get("cost", 0)
        df["profit"] = df["sales"] - (df.get("quantity", 1) * cost)

    # --- Core Totals ---
    metrics["total_revenue"] = round(df["sales"].sum(), 2)
    metrics["total_profit"] = round(df["profit"].sum(), 2)

    metrics["gross_margin_pct"] = round(
        (metrics["total_profit"] / metrics["total_revenue"]) * 100
        if metrics["total_revenue"] > 0 else 0,
        2
    )

    metrics["vat_due"] = round(metrics["total_revenue"] * 0.15, 2)

    # --- Order-Level ---
    metrics["average_order_value"] = round(
        metrics["total_revenue"] / max(len(df), 1), 2
    )

    # --- Product-Level Intelligence ---
    if "product_name" in df.columns:
        grouped = df.groupby("product_name").agg({
            "sales": "sum",
            "profit": "sum",
            "quantity": "sum"
        }).reset_index()

        grouped["margin_pct"] = (
            grouped["profit"] / grouped["sales"] * 100
        ).replace([float("inf"), -float("inf")], 0).fillna(0)

        metrics["top_revenue_items"] = (
            grouped.sort_values("sales", ascending=False)
            .head(5)[["product_name", "sales"]]
            .to_dict("records")
        )

        metrics["top_profit_items"] = (
            grouped.sort_values("profit", ascending=False)
            .head(5)[["product_name", "profit"]]
            .to_dict("records")
        )

        metrics["loss_making_items"] = (
            grouped[grouped["profit"] < 0]
            .sort_values("profit")
            .head(5)[["product_name", "profit"]]
            .to_dict("records")
        )

        metrics["high_volume_low_margin"] = (
            grouped[
                (grouped["quantity"] > grouped["quantity"].median()) &
                (grouped["margin_pct"] < grouped["margin_pct"].median())
            ][["product_name", "quantity", "margin_pct"]]
            .to_dict("records")
        )

    # --- Discount Impact ---
    if "discount" in df.columns:
        metrics["total_discount"] = round(df["discount"].sum(), 2)
        metrics["discount_ratio_pct"] = round(
            (metrics["total_discount"] / metrics["total_revenue"]) * 100
            if metrics["total_revenue"] > 0 else 0,
            2
        )

    return metrics
    # ================= AI INSIGHT NARRATOR =================
def generate_ai_insights(metrics: Dict) -> str:
    if _model is None:
        return "AI insights unavailable (API key not configured)."

    prompt = f"""
You are a business analyst advising a small business owner.

Explain these metrics in simple, actionable language.
Be concise, practical, and honest.
Do NOT invent numbers.

Metrics:
{json.dumps(metrics, indent=2)}

Focus on:
- Profitability risks
- Pricing or discount issues
- What to improve first
"""

    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "AI insight generation failed."
 def resolve_columns(df):
    resolved = {}
    cols = [c.lower().strip() for c in df.columns]

    for canonical, variants in CANONICAL_SCHEMA.items():
        for i, col in enumerate(cols):
            if col == canonical or col in variants:
                resolved[canonical] = df.columns[i]
                break

    return resolved
S       






