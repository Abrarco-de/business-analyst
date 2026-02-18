import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g = Groq(api_key=groq_key)
        m = Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    # Standardize column names
    df.columns = [str(c).strip() for c in df.columns]
    
    # 1. SMART COLUMN MAPPING (Optimized for Supermart Dataset)
    def find_col(targets, blacklist=['id', 'code', 'sku', 'no']):
        # Priority 1: Exact match with target
        for t in targets:
            for c in df.columns:
                if t.lower() == c.lower(): return c
        # Priority 2: Keyword match avoiding blacklist
        for t in targets:
            for c in df.columns:
                if t.lower() in c.lower() and not any(b in c.lower() for b in blacklist):
                    return c
        return df.columns[0]

    r_col = find_col(['Sales', 'Revenue', 'Total Amount'])
    p_col = find_col(['Profit', 'Net Income', 'Gain'])
    prod_col = find_col(['Sub Category', 'Product Name', 'Item', 'Description'], blacklist=['id', 'code'])
    qty_col = find_col(['Quantity', 'Qty', 'Units'], blacklist=['id'])

    # 2. DATA CLEANING
    def to_num(series):
        return pd.to_numeric(series.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)

    df['_rev'] = to_num(df[r_col])
    df['_prof'] = to_num(df[p_col])
    df['_qty'] = to_num(df[qty_col]) if qty_col in df.columns else pd.Series([1]*len(df))

    # 3. ADVANCED CALCULATIONS
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    total_qty = df['_qty'].sum()
    
    # Product Grouping
    prod_stats = df.groupby(prod_col).agg({'_rev': 'sum', '_prof': 'sum', '_qty': 'sum'})
    prod_stats['margin'] = (prod_stats['_prof'] / prod_stats['_rev'] * 100).fillna(0)

    # Sorting for Data Exchange
    top_5_margin = prod_stats.sort_values('margin', ascending=False).head(5)
    bot_5_margin = prod_stats.sort_values('margin', ascending=True).head(5)

    metrics = {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "gross_margin_pct": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "vat_due": round(total_rev * 0.15, 2),
        "avg_transaction": round(total_rev / len(df), 2) if len(df) > 0 else 0,
        "total_units": int(total_qty),
        "rev_per_unit": round(total_rev / total_qty, 2) if total_qty > 0 else 0,
        # Sorted Lists for UI and AI
        "top_margin_list": ", ".join([f"{n} ({v:.1f}%)" for n, v in top_5_margin['margin'].items()]),
        "bot_margin_list": ", ".join([f"{n} ({v:.1f}%)" for n, v in bot_5_margin['margin'].items()]),
        "top_margin_item": top_5_margin.index[0] if not top_5_margin.empty else "N/A",
        "bot_margin_item": bot_5_margin.index[0] if not bot_5_margin.empty else "N/A",
        # Product Category Lists
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.tolist(),
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.tolist(),
        "low_margin": prod_stats.nsmallest(3, 'margin').index.tolist(),
        "high_vol_low_margin": prod_stats[(prod_stats['_qty'] > prod_stats['_qty'].mean()) & (prod_stats['margin'] < 25)].index.tolist()
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    context = f"""
    SME DATA: Rev {metrics['total_revenue']} SAR, Profit {metrics['total_profit']} SAR.
    HIGHEST MARGINS: {metrics['top_margin_list']}
    LEAST MARGINS: {metrics['bot_margin_list']}
    """
    prompt = f"{context}\nUser: {user_query}\nTask: Answer as a Saudi business expert in 2 sentences."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
