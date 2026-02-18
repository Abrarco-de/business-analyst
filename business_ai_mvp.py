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
    
    # 1. Smart Mapping for Supermart File
    r_col = next((c for c in df.columns if 'Sales' in c or 'Revenue' in c), df.columns[0])
    p_col = next((c for c in df.columns if 'Profit' in c), None)
    prod_col = next((c for c in df.columns if 'Sub Category' in c or 'Item' in c), df.columns[0])

    # 2. Cleaning
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    
    # 3. Product Analysis (The "Data Exchange" Fix)
    prod_stats = df.groupby(prod_col).agg({'_rev': 'sum', '_prof': 'sum'})
    prod_stats['margin'] = (prod_stats['_prof'] / prod_stats['_rev'] * 100).fillna(0)

    # We find the absolute extremes instead of using a 10% filter
    least_margin_item = prod_stats['margin'].idxmin()
    least_margin_val = prod_stats['margin'].min()
    
    best_margin_item = prod_stats['margin'].idxmax()
    best_margin_val = prod_stats['margin'].max()

    metrics = {
        "total_revenue": round(df['_rev'].sum(), 2),
        "total_profit": round(df['_prof'].sum(), 2),
        "gross_margin_pct": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2),
        "vat_due": round(df['_rev'].sum() * 0.15, 2),
        "avg_transaction": round(df['_rev'].mean(), 2),
        "total_units": len(df),
        "rev_per_unit": round(df['_rev'].mean(), 2),
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.tolist(),
        # NEW: Absolute Extreme Data Exchange
        "least_margin_name": f"{least_margin_item} ({least_margin_val:.1f}%)",
        "best_margin_name": f"{best_margin_item} ({best_margin_val:.1f}%)",
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.tolist(),
        "low_margin": prod_stats.nsmallest(3, 'margin').index.tolist() # Gives bottom 3 always
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    # This context now GUARANTEES the AI knows the answer
    context = f"""
    SME DATA:
    - Absolute Lowest Margin: {metrics['least_margin_name']}
    - Absolute Highest Margin: {metrics['best_margin_name']}
    - Top Revenue Items: {metrics['top_rev_prods']}
    - Total Profit: {metrics['total_profit']} SAR
    """
    
    prompt = f"{context}\n\nQuestion: {user_query}\n\nTask: Answer briefly using the exact names above."
    
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
