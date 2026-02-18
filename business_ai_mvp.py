import pandas as pd
import numpy as np
import re
from groq import Groq
from mistralai import Mistral

# --- 1. CORE CONFIGURATION ---
def configure_dual_engines(groq_key, mistral_key):
    """Initializes API clients safely."""
    g, m = None, None
    try:
        if groq_key: g = Groq(api_key=groq_key)
        if mistral_key: m = Mistral(api_key=mistral_key)
    except Exception as e:
        print(f"Engine Init Error: {e}")
    return g, m

# --- 2. DATA CLEANING UTILS ---
def clean_currency(series):
    """Converts strings like '$1,200.50' to float."""
    if series is None: return None
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_column(df, keywords, blacklist=[]):
    """Smart column detection with priority and blacklist filtering."""
    cols = [str(c).strip() for c in df.columns]
    
    # Priority 1: Exact Match
    for k in keywords:
        for c in cols:
            if k.lower() == c.lower(): return c
            
    # Priority 2: Keyword match excluding blacklist
    for k in keywords:
        for c in cols:
            if k.lower() in c.lower():
                if not any(b.lower() in c.lower() for b in blacklist):
                    return c
    return None

# --- 3. THE HYBRID RESOLVER ---
def resolve_schema_and_clean(df):
    """
    Determines how to calculate Revenue, Profit, and Dates.
    Logic: If Revenue is missing, look for Price * Qty. 
    If Profit is missing, look for Rev - Cost.
    """
    meta = {"real_profit": False, "has_qty": False, "has_date": False, "profit_method": "Unknown"}

    # A. REVENUE
    rev_col = detect_column(df, ['Sales', 'Revenue', 'Amount', 'Turnover'], blacklist=['tax', 'vat', 'discount'])
    price_col = detect_column(df, ['Price', 'Unit Cost', 'Rate'])
    qty_col = detect_column(df, ['Qty', 'Quantity', 'Units'], blacklist=['id', 'code'])

    if rev_col:
        df['_rev'] = clean_currency(df[rev_col])
    elif price_col and qty_col:
        df['_rev'] = clean_currency(df[price_col]) * clean_currency(df[qty_col])
    else:
        raise ValueError("Could not find 'Sales' or 'Price + Quantity' columns.")

    # B. PROFIT
    prof_col = detect_column(df, ['Profit', 'Net Margin', 'Gain'], blacklist=['%'])
    cost_col = detect_column(df, ['Cost', 'Buying Price', 'Expenses'])
    
    if prof_col:
        df['_prof'] = clean_currency(df[prof_col])
        meta['real_profit'] = True
        meta['profit_method'] = "Actual Data"
    elif cost_col:
        df['_prof'] = df['_rev'] - clean_currency(df[cost_col])
        meta['real_profit'] = True
        meta['profit_method'] = "Calculated (Rev-Cost)"
    else:
        df['_prof'] = df['_rev'] * 0.20 # SME Standard Estimate
        meta['real_profit'] = False
        meta['profit_method'] = "Est. 20% of Sales"

    # C. QUANTITY & DATES
    if qty_col:
        df['_qty'] = clean_currency(df[qty_col])
        meta['has_qty'] = True
    else:
        df['_qty'] = 0

    date_col = detect_column(df, ['Date', 'Time', 'Timestamp', 'Day'])
    if date_col:
        conv_dates = pd.to_datetime(df[date_col], errors='coerce')
        if not conv_dates.isna().all():
            df['_date'] = conv_dates
            meta['has_date'] = True

    # D. PRODUCT NAME
    prod_col = detect_column(df, ['Sub Category', 'Product', 'Item', 'Name'], blacklist=['id', 'code', 'customer'])
    df['_prod'] = df[prod_col].astype(str) if prod_col else df.iloc[:, 0].astype(str)

    return df, meta

# --- 4. DATA PROCESSING ---
def process_business_data(groq_client, df_raw):
    try:
        df, meta = resolve_schema_and_clean(df_raw.copy())
    except Exception as e:
        return {"error": str(e)}, df_raw

    # Aggregate Metrics
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    
    # Product Level Sorting
    p_stats = df.groupby('_prod').agg({'_rev':'sum', '_prof':'sum', '_qty':'sum'})
    p_stats['margin'] = (p_stats['_prof'] / p_stats['_rev'] * 100).fillna(0)
    
    # Significant items only (Filter out tiny noise)
    sig_items = p_stats[p_stats['_rev'] > (total_rev / len(p_stats)) * 0.1]
    if sig_items.empty: sig_items = p_stats

    # Prepare Sorted Lists for UI/AI
    top_margin = sig_items.sort_values('margin', ascending=False).head(5)
    bot_margin = sig_items.sort_values('margin', ascending=True).head(5)
    top_rev = p_stats.sort_values('_rev', ascending=False).head(5)

    # Trend Logic
    trend_dict = {}
    if meta['has_date']:
        # Group by Month, format date for JSON
        monthly = df.set_index('_date')['_rev'].resample('ME').sum()
        trend_dict = {k.strftime('%Y-%m-%d'): v for k, v in monthly.items()}

    metrics = {
        "status": "success",
        "meta": meta,
        "revenue": round(total_rev, 2),
        "profit": round(total_prof, 2),
        "margin_pct": round((total_prof/total_rev*100), 2) if total_rev > 0 else 0,
        "avg_order": round(total_rev / len(df), 2),
        "vat": round(total_rev * 0.15, 2),
        "units": int(df['_qty'].sum()) if meta['has_qty'] else None,
        
        # Sorted Data Strings
        "top_margin_items": [f"{n} ({m:.1f}%)" for n, m in top_margin['margin'].items()],
        "bot_margin_items": [f"{n} ({m:.1f}%)" for n, m in bot_margin['margin'].items()],
        "top_revenue_list": top_rev.index.tolist(),
        "trend_data": trend_dict
    }
    return metrics, df

# --- 5. AI INTERPRETATION ---
def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI not connected."
    
    context = f"""
    SME PERFORMANCE:
    - Rev: {m['revenue']} SAR, Profit: {m['profit']} SAR ({m['meta']['profit_method']})
    - Top Margins: {', '.join(m['top_margin_items'][:3])}
    - Weakest Margins: {', '.join(m['bot_margin_items'][:3])}
    - Best Sellers: {', '.join(m['top_revenue_list'][:3])}
    """
    
    prompt = f"{context}\n\nQuestion: {query}\n\nTask: Act as a Senior Saudi Business Consultant. Answer in 2 professional sentences."
    
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
