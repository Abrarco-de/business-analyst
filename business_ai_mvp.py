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
    # Remove SAR, commas, and other non-numeric chars
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
        
        # Clean numeric columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
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

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(standard_schema.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        ai_mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        # Ensure AI mapping only contains strings to prevent sequence errors
        for k, v in ai_mapping.items():
            if isinstance(v, str): mapping[k] = v
    except:
        pass
        
    return mapping

def generate_insights(df):
    # Ensure math is performed on numeric series only
    def get_clean_col(name):
        series = df.get(name, pd.Series([0.0] * len(df)))
        return pd.to_numeric(series, errors='coerce').fillna(0.0)

    # 1. REVENUE
    # Use 'total_amount' if it exists, otherwise Price * Qty
    if "total_amount" in df.columns:
        total_rev = float(get_clean_col("total_amount").sum())
    else:
        u_price = get_clean_col("unit_price")
        qty = get_clean_col("quantity")
        total_rev = float((u_price * qty).sum())

    # 2. COST
    c_price = get_clean_col("cost_price")
    qty = get_clean_col("quantity")
    total_cost = float((c_price * qty).sum())
    
    is_estimated = False
    if total_cost == 0:
        total_cost = total_rev * 0.65
        is_estimated = True
        
    total_prof = total_rev - total_cost
    vat_amount = total_rev * 0.15 # Saudi 15% VAT
    
    margin = (total_prof / total_rev * 100) if total_rev > 0 else 0
    
    return {
        "total_revenue": round(float(total_rev), 2),
        "total_profit": round(float(total_prof), 2),
        "vat_due": round(float(vat_amount), 2),
        "margin": round(float(margin), 2),
        "is_estimated_cost": is_estimated
    }
