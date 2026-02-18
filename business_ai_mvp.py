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
    if series is None: return None
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords, blacklist=[]):
    cols = [str(c).strip() for c in df.columns]
    for k in keywords:
        for c in cols:
            if k.lower() == c.lower(): return c
    for k in keywords:
        for c in cols:
            if k.lower() in c.lower() and not any(b.lower() in c.lower() for b in blacklist):
                return c
    return None

def process_business_data(groq_client, df_raw):
    try:
        df = df_raw.copy()
        meta = {"real_profit": False, "has_date": False, "has_qty": False, "profit_method": "Estimated"}
        
        # Mapping
        rev_col = detect_col(df, ['Sales', 'Revenue', 'Amount'])
        prof_col = detect_col(df, ['Profit', 'Margin'])
        date_col = detect_col(df, ['Order Date', 'Date'])
        qty_col = detect_col(df, ['Qty', 'Quantity', 'Units'])
        disc_col = detect_col(df, ['Discount', 'Disc'])
        prod_col = detect_col(df, ['Sub Category', 'Product', 'Item']) or df.columns[0]

        if not rev_col: return {"error": "Could not find a Sales or Revenue column."}, df_raw
        
        df['_rev'] = clean_num(df[rev_col])
        
        if prof_col:
            df['_prof'] = clean_num(df[prof_col])
            meta['real_profit'] = True
            meta['profit_method'] = "Actual"
        else:
            df['_prof'] = df['_rev'] * 0.20
            meta['profit_method'] = "Estimated (20%)"

        if qty_col:
            df['_qty'] = clean_num(df[qty_col])
            meta['has_qty'] = True
        else:
            df['_qty'] = 0

        # Date Fix for Supermart (Mixed formats)
        trend_dict = {}
        if date_col:
            # dayfirst=True handles the DD-MM-YYYY format in your Supermart file
            df['_date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            if not df['_date'].isna().all():
                meta['has_date'] = True
                # Use 'ME' for Month End resampling
                monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('ME').sum()
                trend_dict = {k.strftime('%Y-%m-%d'): float(v) for k, v in monthly.items()}

        df['_prod'] = df[prod_col].astype(str)
        stats = df.groupby('_prod').agg({'_rev':'sum', '_prof':'sum', '_qty':'sum'})
        stats['margin'] = (stats['_prof'] / stats['_rev'] * 100).fillna(0)
        
        # High Volume Low Margin
        avg_rev = stats['_rev'].mean()
        hvlm = stats[(stats['_rev'] > avg_rev) & (stats['margin'] < 20)].index.tolist()

        metrics = {
            "status": "success",
            "meta": meta,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0,
            "bot_margin_list": [f"{n} ({m:.1f}%)" for n, m in stats.sort_values('margin').head(5)['margin'].items()],
            "top_margin_list": [f"{n} ({m:.1f}%)" for n, m in stats.sort_values('margin', ascending=False).head(5)['margin'].items()],
            "high_vol_low_margin": hvlm[:5],
            "trend_data": trend_dict,
            "vat_due": float(df['_rev'].sum() * 0.15)
        }
        return metrics, df
    except Exception as e:
        return {"error": f"Engine Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "Mistral API Key missing in secrets."
    ctx = f"Data: Rev {m.get('total_revenue')}, Profit {m.get('total_profit')}. Question: {query}"
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role":"user", "content":ctx}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {e}"
