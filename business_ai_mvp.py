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
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        return None

def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["item", "product", "category", "المنتج", "الصنف"],
        "unit_price": ["price per unit", "unit price", "rate", "سعر الوحدة"],
        "quantity": ["qty", "quantity", "count", "الكمية"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع"],
        "cost_price": ["unit cost", "cost price", "purchase price", "التكلفة"]
    }
    mapping = {}
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(schema_hints.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except:
        for col in columns:
            col_l = col.lower().strip()
            for std, hints in schema_hints.items():
                if any(h in col_l for h in hints):
                    mapping[col] = std
                    break
    return mapping

def generate_insights(df):
    # Revenue Logic (Fixed to prevent 172M error)
    if "total_amount" in df.columns and df["total_amount"].sum() > 0:
        total_rev = df["total_amount"].sum()
    else:
        total_rev = (df.get("unit_price", 0) * df.get("quantity", 0)).sum()

    # Cost Logic
    total_cost = (df.get("cost_price", 0) * df.get("quantity", 0)).sum()
    is_estimated = False
    if total_cost == 0:
        total_cost = total_rev * 0.65
        is_estimated = True
        
    total_prof = total_rev - total_cost
    vat_amount = total_rev * 0.15
    
    return {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "vat_due": round(vat_amount, 2),
        "margin": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "is_estimated_cost": is_estimated
    }
