import pandas as pd
import google.generativeai as genai
import json
import re

def configure_ai(api_key):
    if not api_key:
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"AI Config Error: {e}")
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
        
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amount', 'سعر', 'كمية']):
                df[col] = df[col].apply(clean_numeric_value)
        
        # Standardize Date column
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'تاريخ' in c.lower()]
        if date_cols:
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            
        return df
    except Exception:
        return None

def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["product", "item", "desc", "المنتج", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر"],
        "quantity": ["qty", "quantity", "count", "الكمية"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع"],
        "cost_price": ["unit cost", "cost price", "purchase price", "التكلفة"],
        "date": ["date", "time", "تاريخ"]
    }
    
    mapping = {}
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to {list(schema_hints.keys())}. Return ONLY JSON: {columns}"
        response = model.generate_content(prompt)
        mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
    except Exception:
        # Robust Local Fallback
        for col in columns:
            col_l = col.lower().strip()
            for std, hints in schema_hints.items():
                if any(h == col_l or h in col_l for h in hints):
                    mapping[col] = std
                    break
    return mapping

def generate_insights(df):
    # 1. Base Revenue Calculation (Prevents Double-Counting)
    if "total_amount" in df.columns and df["total_amount"].sum() > 0:
        df['calc_rev'] = df['total_amount']
    elif "unit_price" in df.columns and "quantity" in df.columns:
        df['calc_rev'] = df['unit_price'] * df['quantity']
    elif "unit_price" in df.columns:
        df['calc_rev'] = df['unit_price']
    else:
        df['calc_rev'] = 0.0

    # 2. Cost & Profit Calculation
    if 'cost_price' in df.columns and df['cost_price'].sum() > 0:
        df['calc_cost'] = df['cost_price'] * df.get('quantity', 1)
        is_estimated = False
    else:
        df['calc_cost'] = df['calc_rev'] * 0.65 # Industry Standard for Saudi Retail
        is_estimated = True
    
    df['calc_profit'] = df['calc_rev'] - df['calc_cost']
    total_rev = df['calc_rev'].sum()
    total_prof = df['calc_profit'].sum()
    
    # 3. Product Analysis (Fixed Safety for Line 65)
    prod_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
    
    rev_group = df.groupby(prod_col)['calc_rev'].sum()
    top_revenue_product = rev_group.idxmax() if not rev_group.empty else "N/A"
    
    prof_group = df.groupby(prod_col)['calc_profit'].sum()
    top_profit_product = prof_group.idxmax() if not prof_group.empty else "N/A"
    
    # 4. Growth Metric (1st Half vs 2nd Half)
    growth = 0
    if 'date' in df.columns and not df['date'].isnull().all():
        df_sorted = df.sort_values('date')
        mid = len(df_sorted) // 2
        if mid > 0:
            first_half = df_sorted['calc_rev'].iloc[:mid].sum()
            second_half = df_sorted['calc_rev'].iloc[mid:].sum()
            if first_half > 0:
                growth = ((second_half - first_half) / first_half) * 100
        
    return {
        "total_revenue": round(float(total_rev), 2),
        "total_profit": round(float(total_prof), 2),
        "margin": round((total_prof/total_rev*100), 2) if total_rev > 0 else 0,
        "vat_due": round(total_rev * 0.15, 2),
        "growth_pct": round(growth, 2),
        "top_product_rev": top_revenue_product,
        "top_product_profit": top_profit_product,
        "is_estimated_cost": is_estimated,
        "avg_transaction": round(total_rev / len(df), 2) if len(df) > 0 else 0
    }
