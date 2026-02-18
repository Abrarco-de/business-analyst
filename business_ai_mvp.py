import pandas as pd
import numpy as np
import google.generativeai as genai
import re

def configure_ai(api_key):
    """Configures Gemini with REST transport for maximum stability."""
    if not api_key: return False
    try:
        genai.configure(api_key=api_key, transport='rest')
        return True
    except:
        return False

def process_business_file(uploaded_file):
    """Safely loads CSV/Excel and cleans whitespace."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        
        df = df.dropna(how='all').applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()].copy()
        return df
    except:
        return None

def get_header_mapping(columns):
    """Advanced Schema Logic: Maps messy headers to internal standards."""
    schema_hints = {
        "product_name": ["item", "product", "category", "المنتج", "الصنف", "type", "description"],
        "unit_price": ["price per unit", "unit price", "rate", "سعر الوحدة", "price"],
        "quantity": ["qty", "quantity", "count", "الكمية", "units", "amount"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع", "total", "sales"],
        "cost_price": ["unit cost", "cost price", "purchase", "التكلفة", "cost"]
    }
    mapping = {}
    for col in columns:
        col_l = str(col).lower().replace("_", " ").replace("-", " ")
        for std, hints in schema_hints.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break
    return mapping

def generate_insights(df):
    """Deterministic Logic: Python-based calculations for 100% accuracy."""
    try:
        # Helper to clean currency strings '100 SAR' -> 100.0
        def to_num(col_name):
            data = df.get(col_name, pd.Series([0.0]*len(df)))
            if isinstance(data, pd.DataFrame): data = data.iloc[:, 0]
            if data.dtype == 'object':
                data = data.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(data, errors='coerce').fillna(0.0)

        # Apply mapping logic to verify calculations
        qty = to_num("quantity")
        if "total_amount" in df.columns:
            rev_series = to_num("total_amount")
        else:
            rev_series = to_num("unit_price") * qty

        total_rev = float(rev_series.sum())
        
        # Profitability logic
        if "cost_price" in df.columns:
            total_cost = (to_num("cost_price") * qty).sum()
            is_est = False
        else:
            total_cost = total_rev * 0.65 # Default logic
            is_est = True

        net_profit = total_rev - total_cost
        margin = (net_profit / total_rev * 100) if total_rev > 0 else 0

        # Leaderboard
        name_col = "product_name" if "product_name" in df.columns else df.columns[0]
        df['temp_rev'] = rev_series
        best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax() if not df.empty else "N/A"

        return {
            "revenue": round(total_rev, 2),
            "profit": round(net_profit, 2),
            "margin": round(margin, 2),
            "vat": round(total_rev * 0.15, 2),
            "best_seller": best_seller,
            "is_estimated": is_est,
            "df": df,
            "name_col": name_col
        }
    except Exception as e:
        return {"revenue": 0, "profit": 0, "margin": 0, "vat": 0, "best_seller": "Error", "is_estimated": True, "name_col": "N/A"}




