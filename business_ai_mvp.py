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

    if not valida

