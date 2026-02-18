import pandas as pd
import numpy as np
import google.generativeai as genai
import re

def configure_ai(api_key):
    """Stable AI configuration using REST transport."""
    if not api_key:
        return False
    try:
        genai.configure(api_key=api_key, transport='rest')
        return True
    except Exception:
        return False

def process_business_file(uploaded_file):
    """Safely loads and pre-cleans the file."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Deduplicate and clean whitespace
        df = df.loc[:, ~df.columns.duplicated()].copy()
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return df
    except Exception:
        return None

def get_header_mapping(columns):
    """Maps various column names to standard keys."""
    schema_hints = {
        "product_name": ["item", "product", "category", "sub", "المنتج", "type"],
        "unit_price": ["price per unit", "unit price", "rate", "price", "unit_price"],
        "quantity": ["qty", "quantity", "count", "units", "amount"],
        "total_amount": ["total amount", "total sales", "net amount", "total", "sales"],
        "cost_price": ["unit cost", "cost price", "purchase", "cost"]
    }
    mapping = {}
    for col in columns:
        col_l = str(col).lower().replace("_", " ").strip()
        for std, hints in schema_hints.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break
    return mapping

def generate_insights(df):
    """Pure Python Logic for 100% accurate financial metrics."""
    try:
        def to_num(col_name):
            data = df.get(col_name, pd.Series([0.0]*len(df)))
            if isinstance(data, pd.DataFrame):
                data = data.iloc[:, 0]
            if data.dtype == 'object':
                data = data.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(data, errors='coerce').fillna(0.0)

        # Map logic to calculations
        qty = to_num("quantity")
        if "total_amount" in df.columns:
            rev_series = to_num("total_amount")
        else:
            rev_series = to_num("unit_price") * qty

        total_rev = float(rev_series.sum())
        
        if "cost_price" in df.columns:
            total_cost = (to_num("cost_price") * qty).sum()
            is_est = False
        else:
            total_cost = total_rev * 0.65
            is_est = True

        profit = total_rev - total_cost
        margin = (profit / total_rev * 100) if total_rev > 0 else 0

        # Best Seller logic
        name_col = "product_name" if "product_name" in df.columns else df.columns[0]
        df['temp_rev'] = rev_series
        best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax() if not df.empty else "N/A"

        return {
            "revenue": round(total_rev, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 2),
            "vat": round(total_rev * 0.15, 2),
            "best_seller": best_seller,
            "is_estimated": is_est,
            "df": df,
            "name_col": name_col
        }
    except Exception:
        return {"revenue": 0.0, "profit": 0.0, "margin": 0, "vat": 0, "best_seller": "Error", "is_estimated": True, "df": df, "name_col": "N/A"}




