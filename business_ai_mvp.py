import pandas as pd
import numpy as np
import google.generativeai as genai
import re
import os

def configure_ai(api_key):
    """Stable AI configuration using REST transport for India/Global regions."""
    if not api_key:
        return False
    try:
        # Force REST to prevent the common gRPC/v1beta connection errors
        genai.configure(api_key=api_key, transport='rest')
        return True
    except Exception:
        return False

def process_business_file(uploaded_file):
    """Safely loads CSV or Excel files with encoding protection."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Remove empty rows and duplicate columns
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.duplicated()].copy()
        # Clean string whitespace
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return df
    except Exception:
        return None

def get_header_mapping(columns):
    """Hybrid Logic: Rule-based keyword matching for column schema."""
    schema_hints = {
        "product_name": ["item", "product", "category", "sub", "المنتج", "type", "description"],
        "unit_price": ["price per unit", "unit price", "rate", "price", "unit_price"],
        "quantity": ["qty", "quantity", "count", "units", "amount"],
        "total_amount": ["total amount", "total sales", "net amount", "total", "sales", "revenue"],
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
    """Deterministic Math Engine: Python handles the calculations for accuracy."""
    try:
        def to_num(series_data):
            if isinstance(series_data, pd.DataFrame):
                series_data = series_data.iloc[:, 0]
            if series_data.dtype == 'object':
                series_data = series_data.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(series_data, errors='coerce').fillna(0.0)

        # 1. Identify and Clean Numeric Data
        qty = to_num(df.get("quantity", pd.Series([0.0]*len(df))))
        
        if "total_amount" in df.columns:
            rev_series = to_num(df["total_amount"])
        else:
            u_price = to_num(df.get("unit_price", pd.Series([0.0]*len(df))))
            rev_series = u_price * qty

        df['temp_rev'] = rev_series
        total_rev = float(rev_series.sum())
        
        # 2. Profitability Logic
        if "cost_price" in df.columns:
            cost_series = to_num(df["cost_price"]) * qty
            is_est = False
        else:
            cost_series = rev_series * 0.65
            is_est = True

        profit = total_rev - float(cost_series.sum())
        margin = (profit / total_rev * 100) if total_rev > 0 else 0

        # 3. Dynamic Column Picker for Grouping (Fixes KeyError)
        if "product_name" in df.columns:
            name_col = "product_name"
        else:
            # Fallback to the first text column found
            obj_cols = df.select_dtypes(include=['object']).columns
            name_col = obj_cols[0] if len(obj_cols) > 0 else df.columns[0]

        # 4. Leaderboard Logic
        best_seller = "N/A"
        if not df.empty and total_rev > 0:
            best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax()

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
        # Fallback if everything fails
        return {"revenue": 0.0, "profit": 0.0, "margin": 0, "vat": 0, "best_seller": "Error", "is_estimated": True, "df": df, "name_col": df.columns[0]}



