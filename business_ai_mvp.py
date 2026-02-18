import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g, m = Groq(api_key=groq_key), Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    # Standardize headers
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # --- ADVANCED SEMANTIC MAPPING ---
    def identify_product_col(df):
        scores = {}
        blacklist = ['id', 'code', 'sku', 'no', 'number', 'phone', 'date', 'sl', 'index']
        
        for col in df.columns:
            score = 0
            col_lower = col.lower()
            
            # Rule 1: Keywords in header
            if any(k in col_lower for k in ['name', 'item', 'desc', 'product', 'title']): score += 10
            if any(b in col_lower for b in blacklist): score -= 20
            
            # Rule 2: Content Analysis (Is it mostly text?)
            sample = df[col].dropna().head(10).astype(str)
            if sample.str.contains(r'[a-zA-Z]').mean() > 0.5: score += 10 # Has letters
            if sample.str.isnumeric().mean() > 0.8: score -= 30 # Mostly numbers (likely an ID)
            
            # Rule 3: Uniqueness (Product names repeat, IDs usually don't in sales logs)
            if df[col].nunique() / len(df) > 0.9 and len(df) > 20: score -= 5 
            
            scores[col] = score
        
        return max(scores, key=scores.get)

    def identify_numeric_col(df, keywords):
        for col in df.columns:
            if any(k in col.lower() for k in keywords):
                # Verify it's actually numeric
                sample = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
                if sample.notnull().mean() > 0.5: return col
        return None

    # Final Mapping
    prod_col = identify_product_col(df)
    r_col = identify_numeric_col(df, ['rev', 'sale', 'total', 'amount', 'price']) or df.columns[0]
    p_col = identify_numeric_col(df, ['prof', 'net', 'margin', 'gain'])
    qty_col = identify_numeric_col(df, ['qty', 'unit', 'count', 'quantity', 'sold'])

    # --- CLEANING ---
    def clean_num(col_name):
        if not col_name: return pd.Series([0]*len(df))
        return pd.to_numeric(df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)

    df['_rev'] = clean_num(r_col)
    df['_prof'] = clean_num(p_col) if p_col else df['_rev'] * 0.2
    df['_qty'] = clean_num(qty_col) if qty_col else pd.Series([1]*len(df))

    # --- METRICS ---
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    total_qty = df['_qty'].sum()
    
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
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.astype(str).tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.astype(str).tolist(),
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.astype(str).tolist(),
        "low_margin": prod_stats[(prod_stats['margin'] < 10) & (prod_stats['margin'] > 0)].index.astype(str).tolist(),
        "high_vol_low_margin": prod_stats[(prod_stats['_qty'] > prod_stats['_qty'].mean()) & (prod_stats['margin'] < 15)].index.astype(str).tolist()
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    context = f"SME Data: Rev {metrics['total_revenue']} SAR, Profit {metrics['total_profit']} SAR. Top Profitable: {metrics['top_prof_prods']}. Loss Making: {metrics['loss_making']}."
    prompt = f"{context}\nUser: {user_query}\nTask: Answer as a Saudi business expert in 2 sentences."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
