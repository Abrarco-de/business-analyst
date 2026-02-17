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

def get_header_mapping(columns):
    # Standard schema for Saudi Retail
    schema_hints = {
        "product_name": ["item", "product", "desc", "المنتج", "الصنف", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر", "بيع", "sar"],
        "quantity": ["qty", "count", "amount", "الكمية", "عدد"],
        "cost_price": ["cost", "purchase", "buying", "تكلفة", "شراء"],
        "transaction_id": ["id", "invoice", "receipt", "رقم", "فاتورة"]
    }
    
    mapping = {}
    # Try AI mapping first, but use local hints as fallback instantly
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
    # Calculations
    df['total_sales'] = df.get('unit_price', 0) * df.get('quantity', 0)
    df['total_cost'] = df.get('cost_price', 0) * df.get('quantity', 0)
    
    # 1. Revenue & Profit
    rev = df['total_sales'].sum()
    # Fallback: if cost is 0, estimate 65% COGS for retail
    cost = df['total_cost'].sum() if df['total_cost'].sum() > 0 else (rev * 0.65)
    profit = rev - cost
    
    # 2. ZATCA VAT (15% on Revenue)
    vat_amount = rev * 0.15
    
    # 3. Average Transaction Value (ATV)
    # Using Transaction ID if exists, otherwise average per row
    unique_tx = df['transaction_id'].nunique() if 'transaction_id' in df.columns else len(df)
    atv = rev / unique_tx if unique_tx > 0 else 0
    
    return {
        "total_revenue": round(rev, 2),
        "total_profit": round(profit, 2),
        "margin": round((profit/rev * 100), 2) if rev > 0 else 0,
        "vat_due": round(vat_amount, 2),
        "atv": round(atv, 2),
        "total_items": int(df.get('quantity', 0).sum())
    }
