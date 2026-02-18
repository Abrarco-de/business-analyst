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
        # Clean BOM characters like ï»¿
        df.columns = [c.replace('ï»¿', '').strip() for c in df.columns]
        df = df.dropna(how='all').loc[:, ~df.columns.duplicated()]
        return df
    except: return None

def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["item", "product", "category", "sub", "name", "desc", "particulars"],
        "unit_price": ["price", "rate", "unit"],
        "quantity": ["qty", "quantity", "count", "units", "sold"],
        "total_amount": ["total", "sales", "revenue", "net", "amount"],
        "cost_price": ["cost", "purchase", "buying", "profit"] # Added profit here as a fallback
    }
    mapping = {}
    counts = {}
    for col in columns:
        clean_col = str(col).lower().strip().replace(" ", "_")
        matched = False
        for std, hints in schema_hints.items():
            if any(h in clean_col for h in hints):
                counts[std] = counts.get(std, 0) + 1
                suffix = f"_{counts[std]}" if counts[std] > 1 else ""
                mapping[col] = f"{std}{suffix}"
                matched = True
                break
        if not matched: mapping[col] = col
    return mapping

def generate_insights(df):
    try:
        def to_num(col_name):
            if col_name not in df.columns: return pd.Series([0.0]*len(df))
            series = df[col_name]
            if series.dtype == 'object':
                series = series.astype(str).str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(series, errors='coerce').fillna(0.0)

        # 1. Math Logic
        qty = to_num("quantity")
        rev = to_num("total_amount") if "total_amount" in df.columns else to_num("unit_price") * qty
        df['temp_rev'] = rev
        
        total_rev = float(rev.sum())
        # Use existing Profit column if available (common in retail datasets)
        if "cost_price" in df.columns:
            profit_series = to_num("cost_price") # Mapping 'Profit' column to cost_price logic
            total_profit = float(profit_series.sum())
        else:
            total_profit = total_rev * 0.35
            
        # 2. Smart Best Seller Logic (Looks for the most specific product column)
        # We look for product_name, product_name_2, etc. and pick the one with most unique values
        prod_cols = [c for c in df.columns if "product_name" in c]
        if prod_cols:
            # Pick column with most unique items (usually the actual Product Name vs Category)
            name_col = max(prod_cols, key=lambda x: df[x].nunique())
        else:
            name_col = df.select_dtypes(include=['object']).columns[0]

        best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax() if total_rev > 0 else "N/A"

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




