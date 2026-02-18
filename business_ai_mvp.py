import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g, m = Groq(api_key=groq_key), Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    # 1. CLEAN HEADERS
    df.columns = [str(c).strip() for c in df.columns]
    
    # 2. STRICT COLUMN MAPPING
    # For Supermart file: 'Sales' is Rev, 'Profit' is Prof, 'Sub Category' is Product
    def find_col(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name.lower() == col.lower(): return col
        # Fallback to keyword match
        for name in possible_names:
            for col in df.columns:
                if name.lower() in col.lower(): return col
        return df.columns[0]

    r_col = find_col(['Sales', 'Revenue', 'Amount'])
    p_col = find_col(['Profit', 'Net Margin', 'Gain'])
    # We prioritize 'Sub Category' then 'Category' for product names
    prod_col = find_col(['Sub Category', 'Product', 'Item', 'Category'])

    # 3. FORCE NUMERIC (Cleaning currency symbols etc)
    def to_num(series):
        return pd.to_numeric(series.astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)

    df['_rev'] = to_num(df[r_col])
    df['_prof'] = to_num(df[p_col])
    
    # Safety: If Discount was picked as Sales, Revenue will be tiny. 
    # We check if another column has a much larger sum.
    for col in df.columns:
        if col != r_col and df[col].dtype in ['float64', 'int64']:
            if df[col].sum() > df['_rev'].sum() * 10: # If another col is 10x bigger, it's likely the real Revenue
                df['_rev'] = df[col]

    # 4. ADVANCED METRICS
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    
    prod_stats = df.groupby(prod_col).agg({'_rev': 'sum', '_prof': 'sum'})
    prod_stats['margin'] = (prod_stats['_prof'] / prod_stats['_rev'] * 100).fillna(0)

    metrics = {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "gross_margin_pct": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "vat_due": round(total_rev * 0.15, 2),
        "avg_transaction": round(total_rev / len(df), 2) if len(df) > 0 else 0,
        "total_units": len(df), # In this dataset, 1 row = 1 unit usually
        "rev_per_unit": round(total_rev / len(df), 2) if len(df) > 0 else 0,
        "top_rev_prods": prod_stats['_rev'].nlargest(3).index.tolist(),
        "top_prof_prods": prod_stats['_prof'].nlargest(3).index.tolist(),
        "loss_making": prod_stats[prod_stats['_prof'] < 0].index.tolist(),
        "low_margin": prod_stats[(prod_stats['margin'] < 10)].index.tolist(),
        "high_vol_low_margin": [] # Placeholder for this logic
    }
    return metrics, df

def get_ai_response(mistral_client, metrics, user_query):
    # Pass the real data to the AI
    prompt = f"""
    BUSINESS DATA:
    - Total Revenue: {metrics['total_revenue']} SAR
    - Total Profit: {metrics['total_profit']} SAR
    - Top Items: {metrics['top_prof_prods']}
    
    QUESTION: {user_query}
    INSTRUCTION: Answer as a Saudi Business Consultant in 2 sentences max.
    """
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
