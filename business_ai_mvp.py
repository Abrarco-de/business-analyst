import pandas as pd
import numpy as np
import google.generativeai as genai
import re
import os

def configure_ai(api_key):
    """Forcing REST transport to fix the India/Streamlit connection bug."""
    if not api_key:
        return False
    try:
        # Force REST transport to bypass gRPC errors on cloud servers
        genai.configure(api_key=api_key, transport='rest')
        return True
    except Exception as e:
        print(f"AI Configuration Error: {e}")
        return False

def process_business_file(uploaded_file):
    """Safely loads file and handles potential encoding issues."""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Encoding 'unicode_escape' or 'latin1' handles hidden symbols in CSVs
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Clean empty rows and remove duplicate columns
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.duplicated()].copy()
        return df
    except Exception:
        return None

def get_header_mapping(columns):
    """Maps your dataset columns to the app logic."""
    standard_schema = {
        "product_name": ["item", "product", "category", "sub", "المنتج", "type", "description"],
        "unit_price": ["price per unit", "unit price", "rate", "price", "unit_price"],
        "quantity": ["qty", "quantity", "count", "units", "amount"],
        "total_amount": ["total amount", "total sales", "net amount", "total", "sales", "revenue"],
        "cost_price": ["unit cost", "cost price", "purchase", "cost"]
    }
    mapping = {}
    for col in columns:
        col_l = str(col).lower().strip().replace(" ", "_")
        for std, hints in standard_schema.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break
    return mapping

def generate_insights(df):
    """Calculates metrics while cleaning inconsistent data types."""
    try:
        # 1. Handle Multiple Product Columns (Category + Sub-Category)
        prod_cols = [i for i, col in enumerate(df.columns) if col == 'product_name']
        if len(prod_cols) > 1:
            df['product_name_final'] = df.iloc[:, prod_cols].fillna('General').astype(str).agg(' - '.join, axis=1)
            df = df.drop(df.columns[prod_cols], axis=1)
            df['product_name'] = df['product_name_final']

        # 2. Helper to clean currency strings (e.g., '100 SAR' -> 100.0)
        def to_num(col_name):
            data = df.get(col_name, pd.Series([0.0]*len(df)))
            if isinstance(data, pd.DataFrame): data = data.iloc[:, 0]
            if data.dtype == 'object':
                data = data.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(data, errors='coerce').fillna(0.0)

        # 3. Core Calculations
        df['calc_qty'] = to_num("quantity")
        if "total_amount" in df.columns:
            df['calc_rev'] = to_num("total_amount")
        else:
            df['calc_rev'] = to_num("unit_price") * df['calc_qty']

        rev = float(df['calc_rev'].sum())
        
        if "cost_price" in df.columns:
            df['calc_cost'] = to_num("cost_price") * df['calc_qty']
            is_est = False
        else:
            df['calc_cost'] = df['calc_rev'] * 0.65  # Default 65% cost
            is_est = True

        profit = rev - float(df['calc_cost'].sum())
        margin = (profit / rev * 100) if rev > 0 else 0

        # 4. Results
        name_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
        best_seller = df.groupby(name_col)['calc_qty'].sum().idxmax() if not df.empty else "N/A"
        top_rev_item = df.groupby(name_col)['calc_rev'].sum().idxmax() if not df.empty else "N/A"

        return {
            "revenue": round(rev, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 2),
            "vat": round(rev * 0.15, 2),
            "best_seller": best_seller,
            "most_profitable": top_rev_item,
            "is_estimated": is_est,
            "df": df,
            "name_col": name_col
        }
    except Exception:
        return {"revenue": 0, "profit": 0, "margin": 0, "vat": 0, "best_seller": "Error", "most_profitable": "Error", "is_estimated": True, "df": df, "name_col": "N/A"}
