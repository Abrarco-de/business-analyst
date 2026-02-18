import pandas as pd
import numpy as np
import google.generativeai as genai
import re

def configure_ai(api_key):
    if not api_key: return False
    try:
        genai.configure(api_key=api_key, transport='rest')
        return True
    except: return False

def process_business_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def get_header_mapping(columns):
    # Rule-based detection
    schema_hints = {
        "product_name": ["item", "product", "category", "sub", "name", "desc"],
        "unit_price": ["price", "rate", "unit"],
        "quantity": ["qty", "quantity", "count", "units", "sold"],
        "total_amount": ["total", "sales", "revenue", "net", "amount"],
        "cost_price": ["cost", "purchase", "buying", "profit"]
    }
    mapping = {}
    for col in columns:
        clean_col = str(col).lower().strip().replace(" ", "_")
        for std, hints in schema_hints.items():
            if any(h in clean_col for h in hints):
                mapping[col] = std
                break
    return mapping

def generate_insights(df, mapping_overrides=None):
    """
    Calculates metrics. mapping_overrides allows manual selection from UI.
    """
    try:
        # Use manual selection if provided, else use auto-mapping
        col_map = mapping_overrides if mapping_overrides else {}
        
        def get_col(std_name):
            return col_map.get(std_name, std_name)

        def to_num(col_name):
            if col_name not in df.columns: return pd.Series([0.0]*len(df))
            series = df[col_name]
            if series.dtype == 'object':
                series = series.astype(str).str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(series, errors='coerce').fillna(0.0)

        # CORE MATH
        rev_col = get_col("total_amount")
        qty_col = get_col("quantity")
        
        qty = to_num(qty_col)
        rev = to_num(rev_col) if rev_col in df.columns else (to_num(get_col("unit_price")) * qty)
        
        df['temp_rev'] = rev
        total_rev = float(rev.sum())
        
        # Profit Logic: If user picked 'Profit' column, use it. Else 35% estimate.
        profit_col = get_col("cost_price")
        if profit_col in df.columns:
            total_profit = float(to_num(profit_col).sum())
        else:
            total_profit = total_rev * 0.35

        # Best Seller
        name_col = get_col("product_name")
        best_seller = "N/A"
        if name_col in df.columns and total_rev > 0:
            best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax()

        return {
            "revenue": round(total_rev, 2),
            "profit": round(total_profit, 2),
            "margin": round((total_profit/total_rev*100), 2) if total_rev > 0 else 0,
            "best_seller": best_seller,
            "name_col": name_col,
            "df": df
        }
    except:
        return {"revenue":0, "profit":0, "margin":0, "best_seller":"N/A", "name_col":"None", "df":df}




