import pandas as pd
import numpy as np
import re
from groq import Groq
from mistralai import Mistral

# --- 1. CONFIGURATION & SETUP ---
def configure_dual_engines(groq_key, mistral_key):
    """Initializes API clients safely."""
    g, m = None, None
    try:
        if groq_key: g = Groq(api_key=groq_key)
        if mistral_key: m = Mistral(api_key=mistral_key)
    except Exception as e:
        print(f"API Init Error: {e}")
    return g, m

# --- 2. ROBUST UTILITIES ---
def clean_currency_series(series):
    """Converts string currency (e.g. '$1,200.50') to float safely."""
    if series is None: return None
    # Force to string, remove symbols, convert to numeric
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_column(df, keywords, blacklist=[]):
    """Scans columns using regex and scoring to find the best match."""
    df_cols = [str(c).strip() for c in df.columns]
    best_col = None
    
    # Priority 1: Exact Case-Insensitive Match
    for col in df_cols:
        if col.lower() in [k.lower() for k in keywords]:
            return col
            
    # Priority 2: Partial Match (Validation: Must not be in blacklist)
    for key in keywords:
        for col in df_cols:
            if key.lower() in col.lower():
                # Check blacklist (e.g., avoid 'Product ID' when looking for 'Product')
                if not any(b.lower() in col.lower() for b in blacklist):
                    return col
    return None

# --- 3. SCHEMA RESOLVER ---
def resolve_schema_and_clean(df):
    """
    The Hybrid Resolver: Determines how to calculate Revenue, Profit, and Quantity.
    Returns a cleaned DataFrame with standardized columns: _rev, _prof, _qty, _date, _prod
    """
    # Initialize metadata
    meta = {
        "has_real_profit": False,
        "has_quantity": False,
        "has_date": False,
        "profit_method": "Unknown"
    }

    # A. REVENUE RESOLUTION
    # 1. Look for explicit Total/Sales column
    rev_col = detect_column(df, ['Sales', 'Total Revenue', 'Amount', 'Turnover'], blacklist=['tax', 'vat'])
    
    # 2. Look for Price & Qty if Revenue missing
    price_col = detect_column(df, ['Price', 'Unit Cost', 'MRP'], blacklist=['total'])
    qty_col = detect_column(df, ['Qty', 'Quantity', 'Units', 'Count'], blacklist=['id', 'code'])

    df['_rev'] = 0.0
    
    if rev_col:
        df['_rev'] = clean_currency_series(df[rev_col])
    elif price_col and qty_col:
        # Calculated Revenue
        p = clean_currency_series(df[price_col])
        q = clean_currency_series(df[qty_col])
        df['_rev'] = p * q
    else:
        # Critical Failure
        raise ValueError("Could not detect Revenue data. Need 'Sales' column OR 'Price' + 'Quantity'.")

    # B. PROFIT RESOLUTION
    prof_col = detect_column(df, ['Profit', 'Net Income', 'Margin'], blacklist=['%'])
    cost_col = detect_column(df, ['Cost', 'Buying Price'])
    
    df['_prof'] = 0.0
    
    if prof_col:
        df['_prof'] = clean_currency_series(df[prof_col])
        meta['has_real_profit'] = True
        meta['profit_method'] = "Actual Data"
    elif cost_col and rev_col:
        c = clean_currency_series(df[cost_col])
        df['_prof'] = df['_rev'] - c
        meta['has_real_profit'] = True
        meta['profit_method'] = "Calculated (Rev - Cost)"
    else:
        # Fallback: Estimate 20% (Standard SME Estimate)
        df['_prof'] = df['_rev'] * 0.20
        meta['has_real_profit'] = False
        meta['profit_method'] = "Estimated (20% of Rev)"

    # C. QUANTITY RESOLUTION
    if qty_col:
        df['_qty'] = clean_currency_series(df[qty_col])
        meta['has_quantity'] = True
    else:
        # DO NOT fake quantity. Leave it as None or 0 for logic checks.
        df['_qty'] = 0
        meta['has_quantity'] = False

    # D. DATE & PRODUCT RESOLUTION
    date_col = detect_column(df, ['Date', 'Time', 'Day', 'Month'])
    if date_col:
        try:
            df['_date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            meta['has_date'] = True
        except:
            meta['has_date'] = False

    prod_col = detect_column(df, ['Sub Category', 'Product Name', 'Item', 'Description', 'SKU Name'], blacklist=['id', 'code', 'date'])
    if not prod_col: prod_col = df.columns[0] # Fallback to first col
    df['_prod'] = df[prod_col].astype(str)

    return df, meta

# --- 4. MAIN PROCESSOR ---
def process_business_data(groq_client, df_raw):
    """
    Main entry point. 
    1. Resolves Schema
    2. Calculates Metrics
    3. Prepares Data Exchange Context
    """
    # 1. Resolve Schema
    try:
        df, meta = resolve_schema_and_clean(df_raw.copy())
    except ValueError as e:
        return {"error": str(e)}, df_raw

    # 2. Aggregations
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    total_qty = df['_qty'].sum()
    
    # avoid division by zero
    margin_pct = (total_prof / total_rev * 100) if total_rev > 0 else 0
    avg_order_val = (total_rev / len(df)) if len(df) > 0 else 0
    
    # 3. Product-Level Analysis
    # Group by product to find top/bottom performers
    prod_grp = df.groupby('_prod').agg({
        '_rev': 'sum', 
        '_prof': 'sum',
        '_qty': 'sum'
    })
    prod_grp['margin_pct'] = (prod_grp['_prof'] / prod_grp['_rev'] * 100).fillna(0)
    
    # Sorts
    top_rev = prod_grp.sort_values('_rev', ascending=False).head(3)
    top_prof = prod_grp.sort_values('_prof', ascending=False).head(3)
    
    # For Least Margin, we only look at items with significant sales (ignore $1 items)
    significant_items = prod_grp[prod_grp['_rev'] > prod_grp['_rev'].mean() * 0.1] 
    if significant_items.empty: significant_items = prod_grp
    
    bot_margin = significant_items.sort_values('margin_pct', ascending=True).head(3)
    top_margin = significant_items.sort_values('margin_pct', ascending=False).head(3)

    # 4. Trend Analysis (if date exists)
    trend_data = {}
    if meta['has_date']:
        # Group by Month
        monthly = df.set_index('_date').resample('M')['_rev'].sum()
        trend_data = monthly.to_dict() # {timestamp: revenue}

    # 5. Build Metrics Dictionary
    metrics = {
        "status": "success",
        "meta": meta,
        
        # Financials
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "gross_margin_pct": round(margin_pct, 2),
        "vat_due": round(total_rev * 0.15, 2),
        "avg_order_value": round(avg_order_val, 2),
        
        # Operational (Handle missing Qty)
        "total_units": int(total_qty) if meta['has_quantity'] else None,
        
        # Lists for UI & AI
        "top_revenue_items": top_rev.index.tolist(),
        "top_profit_items": top_prof.index.tolist(),
        
        # Detailed Strings for AI Context
        "lowest_margin_str": ", ".join([f"{n} ({r:.1f}%)" for n, r in bot_margin['margin_pct'].items()]),
        "highest_margin_str": ", ".join([f"{n} ({r:.1f}%)" for n, r in top_margin['margin_pct'].items()]),
        
        # Raw Data for Charts
        "trend_data": trend_data
    }
    
    return metrics, df

# --- 5. AI INTERFACE (Decoupled) ---
def get_ai_response(mistral_client, metrics, user_query):
    if not mistral_client: return "AI Client not initialized."
    if metrics.get('error'): return f"I cannot answer because of data error: {metrics['error']}"

    # Structured Prompt Engineering
    context = f"""
    [DATA CONTEXT]
    - Total Revenue: {metrics['total_revenue']:,.2f}
    - Total Profit: {metrics['total_profit']:,.2f} ({metrics['meta']['profit_method']})
    - Margin: {metrics['gross_margin_pct']}%
    
    [PRODUCT INSIGHTS]
    - Top Sellers: {', '.join(metrics['top_revenue_items'])}
    - Best Margins: {metrics['highest_margin_str']}
    - Lowest Margins: {metrics['lowest_margin_str']}
    """
    
    system_prompt = "You are a Senior Business Analyst. Analyze the provided metrics concisely. Do not hallucinate numbers not present in context."
    
    try:
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nUSER QUESTION: {user_query}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: {str(e)}"
