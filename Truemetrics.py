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

def detect_col(df, keywords):
    cols = [str(c).strip() for c in df.columns]
    for k in keywords:
        for c in cols:
            if k.lower() in c.lower(): return c
    return None

def process_business_data(df_raw):
    try:
        if df_raw is None or df_raw.empty: return {"error": "Empty File"}, None
        df = df_raw.copy()
        mapping_details = []
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price', 'income', 'المبيعات'],
            'Profit': ['profit', 'margin', 'earnings', 'net', 'gain', 'الربح'],
            'Date': ['date', 'time', 'year', 'month', 'التاريخ'],
            'City': ['city', 'region', 'location', 'branch', 'المدينة'],
            'Category': ['category', 'dept', 'group', 'type', 'الفئة'],
            'Product': ['sub category', 'product', 'item', 'description', 'المنتج']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        for k, v in found.items():
            if v: mapping_details.append({"Logic": k, "Header": v, "Sample": str(df[v].iloc[0])})

        if not found['Revenue']: return {"error": "Missing Sales Column"}, df_raw

        df['_rev'] = clean_num(df[found['Revenue']])
        df['_prof'] = clean_num(df[found['Profit']]) if found['Profit'] else df['_rev'] * 0.20
        
        # Distributions
        city_data = df.groupby(found['City'])['_rev'].sum().nlargest(5).to_dict() if found['City'] else {}
        
        # Product Stats
        prod_key = found.get('Product', df.columns[0])
        p_stats = df.groupby(prod_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).fillna(0)

        # Trend Logic (FIXED FOR 'BY' AND 'LEVEL' ERROR)
        trend_dict = {}
        if found['Date']:
            df['_date'] = pd.to_datetime(df[found['Date']], dayfirst=True, errors='coerce')
            if not df['_date'].isna().all():
                # Clean up rows with invalid dates
                temp_df = df.dropna(subset=['_date']).copy()
                try:
                    # Using 'on' or 'rule' depending on library version
                    monthly = temp_df.resample('ME', on='_date')['_rev'].sum()
                except:
                    # Fallback for older pandas versions
                    monthly = temp_df.resample('M', on='_date')['_rev'].sum()
                
                trend_dict = {k.strftime('%b %Y'): float(v) for k, v in monthly.items()}

        return {
            "mapping_preview": mapping_details,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "vat_due": float(df['_rev'].sum() * 0.15),
            "units": len(df),
            "city_dist": city_data,
            "bot_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(3)['m'].items()],
            "top_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(3)['m'].items()],
            "trend_data": trend_dict
        }, df
    except Exception as e: return {"error": str(e)}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI Engine Offline"
    ctx = f"Rev: {m['total_revenue']} SAR, Profit: {m['total_profit']} SAR."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role":"user", "content": f"{ctx}\nQuestion: {query}"}])
        return res.choices[0].message.content
    except: return "Ready."

