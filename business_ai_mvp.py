import pandas as pd
import numpy as np
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    g, m = None, None
    try:
        if groq_key: g = Groq(api_key=groq_key)
        if mistral_key: m = Mistral(api_key=mistral_key)
    except: pass
    return g, m

def clean_num(series):
    if series is None: return 0
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords, blacklist=[]):
    cols = [str(c).strip() for c in df.columns]
    for k in keywords:
        for c in cols:
            if k.lower() == c.lower(): return c
            if k.lower() in c.lower() and not any(b.lower() in c.lower() for b in blacklist):
                return c
    return None

def process_business_data(groq_client, df_raw):
    try:
        df = df_raw.copy()
        meta = {"real_profit": False, "has_date": False, "profit_method": "Estimated"}
        
        # 1. Column Detection
        rev_col = detect_col(df, ['Sales', 'Revenue'])
        prof_col = detect_col(df, ['Profit'])
        date_col = detect_col(df, ['Date', 'Order Date'])
        cat_col = detect_col(df, ['Category'])
        sub_cat_col = detect_col(df, ['Sub Category'])
        city_col = detect_col(df, ['City'])
        qty_col = detect_col(df, ['Qty', 'Quantity', 'Units']) # Check if it exists

        # 2. Basic Cleaning
        df['_rev'] = clean_num(df[rev_col])
        df['_prof'] = clean_num(df[prof_col]) if prof_col else df['_rev'] * 0.20
        df['_qty'] = clean_num(df[qty_col]) if qty_col else 1 # If no Qty, count each row as 1

        # 3. Create a Data Profile for the AI (The "Sharing" part)
        # This tells the AI about every category and city in the file
        profile = {
            "total_orders": len(df),
            "categories": df.groupby(cat_col)['_rev'].sum().to_dict() if cat_col else {},
            "cities": df.groupby(city_col)['_rev'].sum().to_dict() if city_col else {},
            "sub_cat_counts": df.groupby(sub_cat_col).size().to_dict() if sub_cat_col else {}
        }

        # 4. Dates & Margins
        trend_dict = {}
        if date_col:
            df['_date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            if not df['_date'].isna().all():
                meta['has_date'] = True
                try: monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('ME').sum()
                except: monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('M').sum()
                trend_dict = {k.strftime('%Y-%m-%d'): float(v) for k, v in monthly.items()}

        p_stats = df.groupby(sub_cat_col or df.columns[0]).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).fillna(0)
        
        metrics = {
            "status": "success",
            "meta": meta,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "total_units": int(df['_qty'].sum()),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 2) if df['_rev'].sum()>0 else 0,
            "vat_due": float(df['_rev'].sum() * 0.15),
            "bot_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(5)['m'].items()],
            "top_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(5)['m'].items()],
            "trend_data": trend_dict,
            "data_profile": profile # Detailed info for the AI
        }
        return metrics, df
    except Exception as e:
        return {"error": f"Engine Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI not connected."
    
    # We build a massive context string so the AI "knows" everything
    profile = m.get('data_profile', {})
    context = f"""
    You are a Business Intelligence Assistant for a Saudi SME.
    OVERALL: Sales {m['total_revenue']:,.0f}, Profit {m['total_profit']:,.0f}, Units Sold {m['total_units']:,}.
    
    DETAILED DATA MAP:
    - Sales by Category: {profile.get('categories')}
    - Sales by City: {profile.get('cities')}
    - Units/Orders by Sub-Category: {profile.get('sub_cat_counts')}
    
    RULES: 
    1. Use the numbers above to answer questions. 
    2. If asked about a city or category not listed, say you don't have that data.
    3. Keep answers very short (1-2 sentences).
    """
    
    try:
        res = mistral_client.chat.complete(
            model="mistral-large-latest", 
            messages=[{"role":"user", "content": f"{context}\n\nQuestion: {query}"}]
        )
        return res.choices[0].message.content
    except:
        return "The AI is calculating... please try again."
