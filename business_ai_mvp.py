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
        df = df.dropna(how='all').loc[:, ~df.columns.duplicated()]
        return df
    except: return None

def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["item", "product", "category", "sub", "المنتج", "name", "desc"],
        "unit_price": ["price", "rate", "سعر", "unit"],
        "quantity": ["qty", "quantity", "count", "الكمية", "units"],
        "total_amount": ["total", "sales", "revenue", "net", "المجموع"],
        "cost_price": ["cost", "purchase", "buying", "التكلفة"]
    }
    mapping = {}
    counts = {}
    
    for col in columns:
        clean_col = str(col).lower().strip().replace(" ", "_")
        matched = False
        for std, hints in schema_hints.items():
            if any(h in clean_col for h in hints):
                # Handle duplicates by adding a suffix
                counts[std] = counts.get(std, 0) + 1
                suffix = f"_{counts[std]}" if counts[std] > 1 else ""
                mapping[col] = f"{std}{suffix}"
                matched = True
                break
        if not matched:
            mapping[col] = col
    return mapping

def generate_insights(df):
    """Market-ready math engine with self-healing column detection."""
    try:
        def to_num(series_data):
            if series_data is None: return pd.Series([0.0]*len(df))
            if series_data.dtype == 'object':
                # Removes SAR, $, commas, and spaces
                series_data = series_data.astype(str).str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(series_data, errors='coerce').fillna(0.0)

        # 1. SMART EXTRACTION: If 'total_amount' is missing, find it or calculate it
        qty = to_num(df.get("quantity"))
        
        if "total_amount" in df.columns:
            rev_series = to_num(df["total_amount"])
        elif "unit_price" in df.columns:
            rev_series = to_num(df["unit_price"]) * qty
        else:
            # Fallback: Look for ANY column with 'amount' or 'total' in the name
            fallback_cols = [c for c in df.columns if 'amt' in c.lower() or 'total' in c.lower()]
            rev_series = to_num(df[fallback_cols[0]]) if fallback_cols else pd.Series([0.0]*len(df))

        df['temp_rev'] = rev_series
        total_rev = float(rev_series.sum())
        
        # 2. PROFIT LOGIC
        cost_val = to_num(df["cost_price"]).sum() if "cost_price" in df.columns else total_rev * 0.65
        profit = total_rev - cost_val

        # 3. COLUMN PICKER
        obj_cols = df.select_dtypes(include=['object']).columns
        name_col = "product_name" if "product_name" in df.columns else (obj_cols[0] if len(obj_cols)>0 else df.columns[0])

        best_seller = "N/A"
        if not df.empty and total_rev > 0:
            best_seller = df.groupby(name_col)['temp_rev'].sum().idxmax()

        return {
            "revenue": round(total_rev, 2),
            "profit": round(profit, 2),
            "margin": round((profit/total_rev*100), 2) if total_rev > 0 else 0,
            "vat": round(total_rev * 0.15, 2),
            "best_seller": best_seller,
            "is_estimated": "cost_price" not in df.columns,
            "df": df,
            "name_col": name_col
        }
    except:
        return {"revenue":0, "profit":0, "margin":0, "vat":0, "best_seller":"N/A", "is_estimated":True, "df":df, "name_col":df.columns[0]}




