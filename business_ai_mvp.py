import pandas as pd
import google.generativeai as genai
import json
import re

def configure_ai(api_key):
    """Initializes the Gemini AI with the provided API Key."""
    if not api_key:
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"AI Configuration Error: {e}")
        return False

def clean_numeric_value(val):
    """Cleans currency symbols and commas from data."""
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    clean = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

def process_business_file(uploaded_file):
    """Reads CSV/Excel and cleans numeric columns."""
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'تاريخ' in c.lower()]
        if date_cols:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
        return df
    except:
        return None

def get_header_mapping(columns):
    """Uses AI to match user columns to app logic."""
    schema_hints = {
        "product_name": ["product", "item", "desc", "المنتج", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر"],
        "quantity": ["qty", "quantity", "count", "الكمية"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع"],
        "cost_price": ["unit cost", "cost price", "purchase price", "التكلفة"],
        "date": ["date", "time", "تاريخ"]
    }
    try:
        # Crucial: Ensure genai is defined and used correctly
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(schema_hints.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except:
        # Fallback if AI fails
        mapping = {}
        for col in columns:
            col_l = col.lower().strip()
            for std, hints in schema_hints.items():
                if any(h in col_l for h in hints):
                    mapping[col] = std
        return mapping

def generate_insights(df):
    """Calculates Revenue, Profit, Growth, and Top Products."""
    # 1. Revenue Priority Logic
    if "total_amount" in df.columns and df["total_amount"].sum() > 0:
        df['calc_rev'] = df['total_amount']
    elif "unit_price" in df.columns and "quantity" in df.columns:
        df['calc_rev'] = df['unit_price'] * df['quantity']
    else:
        df['calc_rev'] = df.get('unit_price', 0)

    # 2. Cost & Profit (Fallback to 65% COGS)
    if 'cost_price' in df.columns and df['cost_price'].sum() > 0:
        df['calc_cost'] = df['cost_price'] * df.get('quantity', 1)
        is_estimated = False
    else:
        df['calc_cost'] = df['calc_rev'] * 0.65 
        is_estimated = True
    
    df['calc_profit'] = df['calc_rev'] - df['calc_cost']
    
    # 3. Aggregates
    total_rev = df['calc_rev'].sum()
    total_prof = df['calc_profit'].sum()
    
    # 4. Product Analysis (Safety Check for idxmax)
    prod_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
    rev_group = df.groupby(prod_col)['calc_rev'].sum()
    top_prod = rev_group.idxmax() if not rev_group.empty else "N/A"
    
    # 5. Growth Metric
    growth = 0
    if 'date' in df.columns and not df['date'].isnull().all():
        df_s = df.sort_values('date')
        mid = len(df_s) // 2
        f_half = df_s['calc_rev'].iloc[:mid].sum()
        s_half = df_s['calc_rev'].iloc[mid:].sum()
        if f_half > 0: growth = ((s_half - f_half) / f_half) * 100
        
    return {
        "total_revenue": round(float(total_rev), 2),
        "total_profit": round(float(total_prof), 2),
        "margin": round((total_prof/total_rev*100), 2) if total_rev > 0 else 0,
        "vat_due": round(total_rev * 0.15, 2),
        "growth_pct": round(growth, 2),
        "top_product": top_prod,
        "is_estimated_cost": is_estimated,
        "avg_transaction": round(total_rev / len(df), 2) if len(df) > 0 else 0
    }
