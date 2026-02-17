import pandas as pd
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION ---
def configure_ai(api_key):
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

# --- 2. DATA PROCESSING (The missing function) ---
def clean_numeric_value(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    clean = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

def process_business_file(uploaded_file):
    """Reads CSV/Excel and cleans it immediately."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Clean numeric columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

# --- 3. ANALYSIS & INSIGHTS ---
def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["item", "product", "desc", "المنتج", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر", "sar"],
        "quantity": ["qty", "count", "amount", "الكمية"],
        "cost_price": ["cost", "purchase", "تكلفة", "شراء"]
    }
    
    mapping = {}
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(schema_hints.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except:
        # Fallback to simple matching if AI fails
        for col in columns:
            col_l = col.lower().strip()
            for std, hints in schema_hints.items():
                if any(h in col_l for h in hints):
                    mapping[col] = std
                    break
    return mapping

def generate_insights(df):
    rev = (df.get('unit_price', 0) * df.get('quantity', 0)).sum()
    cost = (df.get('cost_price', 0) * df.get('quantity', 0)).sum()
    
    # If no cost data, estimate 65% as a business default
    if cost == 0: cost = rev * 0.65
    
    profit = rev - cost
    vat = rev * 0.15 # ZATCA Standard
    
    return {
        "total_revenue": round(rev, 2),
        "total_profit": round(profit, 2),
        "vat_due": round(vat, 2),
        "margin": round((profit/rev * 100), 2) if rev > 0 else 0
    }
