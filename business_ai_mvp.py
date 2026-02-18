import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g, m = Groq(api_key=groq_key), Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    # Standardize columns
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # 1. Smart Column Detection
    def find_col(keys, avoid=['id', 'code', 'sku']):
        for c in df.columns:
            if any(k in c for k in keys) and not (any(a in c for a in avoid) and len(keys) > 1):
                return c
        return df.columns[0]

    r_col = find_col(['rev', 'sale', 'total', 'amount'])
    p_col = find_col(['prof', 'net', 'margin'])
    prod_col = find_col(['name', 'item', 'desc', 'product'])
    qty_col = find_col(['qty', 'unit', 'count', 'quantity'])

    # 2. Data Cleaning
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col in df.columns else df['_rev'] * 0.2
    df['_qty'] = pd.to_numeric(df[qty_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(1) if qty_col in df.columns else 1

    # 3. Advanced Calculations
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    total_qty = df['_qty'].sum()
    
    # Product Grouping
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
        # Lists for Data Exchange
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.tolist(),
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.tolist(),
        "low_margin": prod_stats[(prod_stats['margin'] < 10) & (prod_stats['margin'] > 0)].index.tolist(),
        "high_vol_low_margin": prod_stats[(prod_stats['_qty'] > prod_stats['_qty'].mean()) & (prod_stats['margin'] < 15)].index.tolist()
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    context = f"""
    DATA: Rev: {metrics['total_revenue']} SAR, Profit: {metrics['total_profit']} SAR.
    TOP PROFIT: {metrics['top_prof_prods']}. LOSS MAKING: {metrics['loss_making']}.
    HIGH VOL/LOW MARGIN: {metrics['high_vol_low_margin']}.
    """
    prompt = f"{context}\nUser: {user_query}\nTask: Answer briefly as a Saudi SME Consultant."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
