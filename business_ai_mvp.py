import pandas as pd
import re
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g, m = Groq(api_key=groq_key), Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    # Standardize columns to lowercase and remove spaces
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # --- 1. SMART COLUMN DETECTION (THE FIX) ---
    def find_best_col(target_keys, blacklist=[]):
        # Step A: Find columns matching target but NOT in blacklist
        potential = [c for c in df.columns if any(k in c for k in target_keys)]
        filtered = [c for c in potential if not any(b in c for b in blacklist)]
        
        if filtered: return filtered[0] # Best match (e.g., 'product_name')
        if potential: return potential[0] # Fallback (e.g., 'product_id')
        return df.columns[0] # Absolute fallback

    # Better mapping logic
    prod_col = find_best_col(['name', 'desc', 'item', 'title'], blacklist=['id', 'code', 'sku', 'no', 'number'])
    r_col = find_best_col(['rev', 'sale', 'total', 'amount', 'price'], blacklist=['tax', 'vat', 'unit'])
    p_col = find_best_col(['prof', 'net', 'margin', 'gain'])
    qty_col = find_best_col(['qty', 'unit', 'count', 'quantity', 'sold'])

    # --- 2. DATA CLEANING ---
    def clean_num(col_name):
        if col_name not in df.columns: return pd.Series([0]*len(df))
        return pd.to_numeric(df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)

    df['_rev'] = clean_num(r_col)
    df['_prof'] = clean_num(p_col) if p_col in df.columns else df['_rev'] * 0.2
    df['_qty'] = clean_num(qty_col) if qty_col in df.columns else pd.Series([1]*len(df))

    # --- 3. ADVANCED METRICS ---
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    total_qty = df['_qty'].sum()
    
    # Grouping by the "Cleaned" Product Name
    prod_stats = df.groupby(prod_col).agg({'_rev': 'sum', '_prof': 'sum', '_qty': 'sum'})
    prod_stats['margin'] = (prod_stats['_prof'] / prod_stats['_rev'] * 100).fillna(0)

    metrics = {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "gross_margin_pct": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "vat_due": round(total_rev * 0.15, 2),
        "avg_transaction": round(total_rev / len(df), 2) if len(df) > 0 else 0,
        "total_units": int(total_qty),
        "rev_per_unit": round(total_rev / total_qty, 2) if total_qty > 0 else 0,
        # Display Lists
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.astype(str).tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.astype(str).tolist(),
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.astype(str).tolist(),
        "low_margin": prod_stats[(prod_stats['margin'] < 10) & (prod_stats['margin'] > 0)].index.astype(str).tolist(),
        "high_vol_low_margin": prod_stats[(prod_stats['_qty'] > prod_stats['_qty'].mean()) & (prod_stats['margin'] < 15)].index.astype(str).tolist()
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    context = f"""
    SME DATA: Rev {metrics['total_revenue']} SAR, Profit {metrics['total_profit']} SAR.
    TOP PROFIT PRODUCTS: {', '.join(metrics['top_prof_prods'])}.
    LOW MARGIN ITEMS: {', '.join(metrics['low_margin'])}.
    """
    prompt = f"{context}\nUser Query: {user_query}\nAnswer as a professional Saudi business analyst in 2 sentences."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
