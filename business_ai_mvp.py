import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import re

def configure_ai(api_key):
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

def clean_numeric_value(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    clean = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

def process_business_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        df = df.loc[:, ~df.columns.duplicated()].copy()
        return df
    except:
        return None

def get_header_mapping(columns):
    standard_schema = {
        "product_name": ["item", "product", "category", "desc", "المنتج", "الصنف"],
        "unit_price": ["price per unit", "unit price", "rate", "سعر الوحدة", "price"],
        "quantity": ["qty", "quantity", "count", "الكمية", "عدد"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع", "total"],
        "cost_price": ["unit cost", "cost price", "purchase", "التكلفة", "cost"]
    }
    mapping = {}
    for col in columns:
        col_l = str(col).lower().strip()
        for std, hints in standard_schema.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break
    
    # AI Fallback
    try:
        # Changed to the most stable model name
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(standard_schema.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        ai_mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        for k, v in ai_mapping.items():
            if k in columns: mapping[k] = v
    except:
        pass # Use local mapping if AI fails
    return mapping

def generate_insights(df):
    def get_num(col_name):
        return pd.to_numeric(df.get(col_name, pd.Series([0.0]*len(df))), errors='coerce').fillna(0.0)

    df['calc_qty'] = get_num("quantity")
    if "total_amount" in df.columns:
        df['calc_rev'] = get_num("total_amount")
    else:
        df['calc_rev'] = get_num("unit_price") * df['calc_qty']
    
    if "cost_price" in df.columns:
        df['calc_cost'] = get_num("cost_price") * df['calc_qty']
        is_est = False
    else:
        df['calc_cost'] = df['calc_rev'] * 0.65
        is_est = True
        
    df['calc_profit'] = df['calc_rev'] - df['calc_cost']
    name_col = "product_name" if "product_name" in df.columns else df.columns[0]
    
    # Safety check for empty data
    best_seller = df.groupby(name_col)['calc_qty'].sum().idxmax() if not df.empty else "N/A"
    most_profitable = df.groupby(name_col)['calc_profit'].sum().idxmax() if not df.empty else "N/A"
    
    return {
        "revenue": round(float(df['calc_rev'].sum()), 2),
        "profit": round(float(df['calc_profit'].sum()), 2),
        "margin": round(float((df['calc_profit'].sum() / df['calc_rev'].sum() * 100)), 2) if df['calc_rev'].sum() > 0 else 0,
        "vat": round(float(df['calc_rev'].sum() * 0.15), 2),
        "best_seller": best_seller,
        "most_profitable": most_profitable,
        "is_estimated": is_est,
        "df": df,
        "name_col": name_col
    }
