import pandas as pd
import numpy as np
import google.generativeai as genai
import time

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
        # Standardize: strip spaces and BOM
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def get_mapped_data(df):
    """Specific mapping for your Supermart, Sales-Data, and Retail files."""
    cols = df.columns
    # 1. Product Name Detection
    p_options = ["Product Category", "Product", "Sub Category", "Category", "item"]
    p_col = next((c for c in cols if any(opt.lower() in c.lower() for opt in p_options)), cols[0])
    
    # 2. Revenue Detection
    r_options = ["Total Amount", "Sales", "Revenue"]
    r_col = next((c for c in cols if any(opt.lower() in c.lower() for opt in r_options)), None)
    
    # 3. Price & Qty fallback
    pr_col = next((c for c in cols if "price" in c.lower()), None)
    qty_col = next((c for c in cols if "qty" in c.lower() or "quantity" in c.lower()), None)
    
    # 4. Profit Detection
    f_col = next((c for c in cols if "profit" in c.lower()), None)

    # Aggressive cleaning function
    def clean(c):
        if c is None or c not in df.columns: return pd.Series([0.0]*len(df))
        return pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)

    # Calculations
    if r_col:
        revenue = clean(r_col)
    elif pr_col and qty_col:
        revenue = clean(pr_col) * clean(qty_col)
    else:
        revenue = pd.Series([0.0]*len(df))

    if f_col:
        profit = clean(f_col)
    else:
        profit = revenue * 0.25 # Assume 25% if missing

    df['_calc_rev'] = revenue
    df['_calc_prof'] = profit
    
    return df, p_col

def calculate_metrics(df, p_col):
    """Calculates all KPI metrics using Python logic."""
    total_rev = df['_calc_rev'].sum()
    total_prof = df['_calc_prof'].sum()
    zatca_vat = total_rev * 0.15 # Saudi 15% VAT
    
    # Best Seller (Revenue)
    best_seller = df.groupby(p_col)['_calc_rev'].sum().idxmax() if total_rev > 0 else "N/A"
    
    # Highest Profit Product
    top_profit_prod = df.groupby(p_col)['_calc_prof'].sum().idxmax() if total_prof > 0 else "N/A"
    
    return {
        "revenue": round(total_rev, 2),
        "profit": round(total_prof, 2),
        "vat": round(zatca_vat, 2),
        "margin": round((total_prof/total_rev*100), 1) if total_rev > 0 else 0,
        "best_seller": best_seller,
        "top_profit_prod": top_profit_prod
    }

def get_code_insights(metrics, df, p_col):
    """Deterministic business insights calculated by code."""
    top_rev = df.groupby(p_col)['_calc_rev'].sum().max()
    percentage = round((top_rev / metrics['revenue'] * 100), 1) if metrics['revenue'] > 0 else 0
    
    insights = [
        f"✅ **Market Dominance:** Your top product **{metrics['best_seller']}** contributes **{percentage}%** of total sales.",
        f"✅ **Tax Liability:** Estimated ZATCA VAT for this period is **{metrics['vat']:,} SAR**.",
        f"✅ **Efficiency:** You are operating at a **{metrics['margin']}%** net profit margin."
    ]
    return insights


