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
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Clean numeric-looking columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        
        # Remove duplicate columns if any (Market entry safety)
        df = df.loc[:, ~df.columns.duplicated()].copy()
        return df
    except Exception:
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
    # Rule-based matching (100% reliable)
    for col in columns:
        col_l = str(col).lower().strip()
        for std, hints in standard_schema.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break

    # AI Enhancement (Optional)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(standard_schema.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        ai_mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        for k, v in ai_mapping.items():
            if isinstance(v, str) and k in columns: 
                mapping[k] = v
    except:
        pass
    return mapping

def generate_insights(df):
    def get_num(col_name):
        return pd.to_numeric(df.get(col_name, pd.Series([0.0]*len(df))), errors='coerce').fillna(0.0)

    # 1. Revenue Logic
    if "total_amount" in df.columns:
        total_rev = float(get_num("total_amount").sum())
    else:
        total_rev = float((get_num("unit_price") * get_num("quantity")).sum())

    # 2. Cost Logic
    total_cost = float((get_num("cost_price") * get_num("quantity")).sum())
    is_est = False
    if total_cost == 0:
        total_cost = total_rev * 0.65 # Saudi Market Standard COGS
        is_est = True

    profit = total_rev - total_cost
    margin = (profit / total_rev * 100) if total_rev > 0 else 0
    vat = total_rev * 0.15 # ZATCA Saudi VAT

    return {
        "revenue": round(total_rev, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 2),
        "vat": round(vat, 2),
        "is_estimated": is_est,
        "raw_data": df # Returned for charting
    }

