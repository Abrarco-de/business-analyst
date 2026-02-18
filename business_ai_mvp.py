import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g, m = Groq(api_key=groq_key), Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    df.columns = [str(c).strip() for c in df.columns]
    
    # 1. Smart Mapping
    r_col = next((c for c in df.columns if 'Sales' in c or 'Revenue' in c), df.columns[0])
    p_col = next((c for c in df.columns if 'Profit' in c), None)
    # Target 'Sub Category' for this dataset specifically, then fallback
    prod_col = next((c for c in df.columns if 'Sub Category' in c or 'Item' in c or 'Product' in c), df.columns[0])

    # 2. Numeric Cleaning
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    
    # 3. Aggregation & Sorting
    prod_stats = df.groupby(prod_col).agg({'_rev': 'sum', '_prof': 'sum'})
    prod_stats['margin'] = (prod_stats['_prof'] / prod_stats['_rev'] * 100).fillna(0)

    # CREATE SORTED LISTS
    top_5_margin = prod_stats.sort_values('margin', ascending=False).head(5)
    bot_5_margin = prod_stats.sort_values('margin', ascending=True).head(5)

    # Format for Data Exchange
    top_str = ", ".join([f"{n} ({v:.2f}%)" for n, v in top_5_margin['margin'].items()])
    bot_str = ", ".join([f"{n} ({v:.2f}%)" for n, v in bot_5_margin['margin'].items()])

    metrics = {
        "total_revenue": round(df['_rev'].sum(), 2),
        "total_profit": round(df['_prof'].sum(), 2),
        "gross_margin_pct": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2),
        "vat_due": round(df['_rev'].sum() * 0.15, 2),
        "avg_transaction": round(df['_rev'].mean(), 2),
        "total_units": len(df),
        "rev_per_unit": round(df['_rev'].mean(), 2),
        # DATA EXCHANGE FIELDS
        "top_margin_list": top_str,
        "bot_margin_list": bot_str,
        "top_margin_item": top_5_margin.index[0],
        "bot_margin_item": bot_5_margin.index[0]
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    # Pass the EXACT sorted values to the AI
    context = f"""
    BUSINESS INTEL:
    - HIGHEST MARGIN PRODUCTS (Sorted): {metrics['top_margin_list']}
    - LEAST MARGIN PRODUCTS (Sorted): {metrics['bot_margin_list']}
    - Total Profit: {metrics['total_profit']} SAR
    """
    
    prompt = f"{context}\n\nUser Question: {user_query}\n\nTask: Use the sorted lists above to give a specific answer. Be brief (2 sentences)."
    
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
