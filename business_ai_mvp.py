import pandas as pd
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
        # Expanded keywords to catch more column types
        clean_keywords = ['price', 'cost', 'qty', 'quant', 'total', 'amount', 'سعر', 'كمية', 'مبلغ']
        for col in df.columns:
            if any(k in col.lower() for k in clean_keywords):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        return None

def get_header_mapping(columns):
    """Hybrid Mapper: Uses Local Rules first, then AI for improvement."""
    standard_schema = {
        "product_name": ["item", "product", "category", "desc", "المنتج", "الصنف"],
        "unit_price": ["unit price", "price per", "rate", "سعر الوحدة", "price"],
        "quantity": ["qty", "quantity", "count", "الكمية", "عدد"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع", "total"],
        "cost_price": ["unit cost", "cost price", "purchase", "التكلفة", "cost"]
    }
    
    # 1. Start with Local Logic (Reliable)
    mapping = {}
    for col in columns:
        col_l = col.lower().strip()
        for std, hints in standard_schema.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break

    # 2. Try to improve with AI (Optional)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(standard_schema.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        ai_mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        mapping.update(ai_mapping) # AI fills in the gaps
    except:
        pass # If AI fails, we already have our local mapping
        
    return mapping

def generate_insights(df):
    # We use .get() but provide a Series of 0s as a fallback for math
    zero_series = pd.Series([0] * len(df))
    
    # Check for Total column first (to fix the 172M error)
    if "total_amount" in df.columns and df["total_amount"].sum() > 0:
        total_rev = df["total_amount"].sum()
    else:
        # Fallback to Price * Qty
        u_price = df.get("unit_price", zero_series)
        qty = df.get("quantity", zero_series)
        total_rev = (u_price * qty).sum()

    # Cost Calculation
    c_price = df.get("cost_price", zero_series)
    qty = df.get("quantity", zero_series)
    total_cost = (c_price * qty).sum()
    
    # Default 65% cost if no cost data is found
    is_estimated = False
    if total_cost == 0:
        total_cost = total_rev * 0.65
        is_estimated = True
        
    total_prof = total_rev - total_cost
    vat_amount = total_rev * 0.15 # 15% ZATCA
    
    return {
        "total_revenue": round(float(total_rev), 2),
        "total_profit": round(float(total_prof), 2),
        "vat_due": round(float(vat_amount), 2),
        "margin": round(float((total_prof / total_rev * 100)), 2) if total_rev > 0 else 0,
        "is_estimated_cost": is_estimated
    }
