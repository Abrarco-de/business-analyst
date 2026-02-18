import pandas as pd
import numpy as np
import re

def process_business_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except:
        return None

def get_mapped_data(df):
    """Detects and cleans columns for Supermart, Sales-Data, and Retail files."""
    cols = df.columns
    
    # 1. Detect Product Column
    p_options = ["Product Category", "Product", "Sub Category", "Category", "item"]
    p_col = next((c for c in cols if any(opt.lower() in c.lower() for opt in p_options)), cols[0])
    
    # 2. Aggressive Cleaning Helper
    def clean_num(c):
        if c is None or c not in df.columns: return pd.Series([0.0]*len(df))
        return pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)

    # 3. Detect Revenue (Total Amount vs Price*Qty)
    r_col = next((c for c in cols if any(x in c.lower() for x in ["total amount", "sales", "revenue"])), None)
    
    if r_col:
        df['_calc_rev'] = clean_num(r_col)
    else:
        pr_col = next((c for c in cols if "price" in c.lower()), None)
        qty_col = next((c for c in cols if "qty" in c.lower() or "quant" in c.lower()), None)
        df['_calc_rev'] = clean_num(pr_col) * clean_num(qty_col)

    # 4. Detect Profit
    f_col = next((c for c in cols if "profit" in c.lower()), None)
    if f_col:
        df['_calc_prof'] = clean_num(f_col)
    else:
        df['_calc_prof'] = df['_calc_rev'] * 0.25 # 25% fallback
        
    return df, p_col

def calculate_metrics(df, p_col):
    """Calculates ZATCA VAT and highest profit product."""
    total_rev = df['_calc_rev'].sum()
    total_prof = df['_calc_prof'].sum()
    
    # Best Seller & Most Profitable
    best_seller = "N/A"
    most_profitable = "N/A"
    if total_rev > 0:
        best_seller = str(df.groupby(p_col)['_calc_rev'].sum().idxmax())
        most_profitable = str(df.groupby(p_col)['_calc_prof'].sum().idxmax())

    return {
        "revenue": round(total_rev, 2),
        "profit": round(total_prof, 2),
        "zatca": round(total_rev * 0.15, 2),
        "margin": round((total_prof/total_rev*100), 1) if total_rev > 0 else 0,
        "best_seller": best_seller,
        "top_profit_prod": most_profitable
    }

def get_code_insights(metrics, df, p_col):
    """Text insights generated purely by Python logic."""
    top_rev = df.groupby(p_col)['_calc_rev'].sum().max()
    share = round((top_rev / metrics['revenue'] * 100), 1) if metrics['revenue'] > 0 else 0
    
    return [
        f"✅ **Revenue Leader:** {metrics['best_seller']} generates {share}% of your total income.",
        f"✅ **ZATCA Estimate:** You should set aside **{metrics['zatca']:,} SAR** for 15% VAT.",
        f"✅ **Profitability:** Your current operation is yielding a **{metrics['margin']}%** margin."
    ]
    
