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
            'City': ['city', 'region', 'location', 'branch', 'store', 'المدينة'],
            'Category': ['category', 'dept', 'group', 'type', 'الفئة'],
            'Product': ['sub category', 'product', 'item', 'description', 'المنتج']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        for k, v in found.items():
            if v: mapping_details.append({"Logic": k, "Header": v, "Sample": str(df[v].iloc[0])})

        if not found['Revenue']: return {"error": "Missing Sales Column"}, df_raw

        df['_rev'] = clean_num(df[found['Revenue']])
        df['_prof'] = clean_num(df[found['Profit']]) if found['Profit'] else df['_rev'] * 0.20
        
        city_key = found['City'] if found['City'] else None
        city_dist = df.groupby(by=city_key)['_rev'].sum().nlargest(6).to_dict() if city_key else {}
        
        prod_key = found['Product'] if found['Product'] else df.columns[0]
        p_stats = df.groupby(by=prod_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).replace([np.inf, -np.inf], 0).fillna(0)

        trend_dict = {}
        forecast_val = 0
        if found['Date']:
            df['_dt'] = pd.to_datetime(df[found['Date']], dayfirst=True, errors='coerce')
            temp_df = df.dropna(subset=['_dt']).copy()
            if not temp_df.empty:
                temp_df['Month_Year'] = temp_df['_dt'].dt.strftime('%Y-%m')
                monthly_sum = temp_df.groupby('Month_Year')['_rev'].sum().sort_index()
                trend_dict = {pd.to_datetime(k).strftime('%b %Y'): float(v) for k, v in monthly_sum.items()}
                
                # Forecasting: 3-Month Moving Average
                if len(monthly_sum) >= 3:
                    forecast_val = monthly_sum.iloc[-3:].mean()
                elif len(monthly_sum) > 0:
                    forecast_val = monthly_sum.iloc[-1]

        return {
            "mapping_preview": mapping_details,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "vat_due": float(df['_rev'].sum() * 0.15),
            "units": len(df),
            "city_dist": city_dist,
            "forecast": float(forecast_val),
            "bot_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(4)['m'].items()],
            "top_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(4)['m'].items()],
            "trend_data": trend_dict
        }, df
    except Exception as e: return {"error": f"Engine Logic Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI Engine Offline. Check Secrets."
    ctx = f"""
    You are an expert Data Consultant analyzing this dataset:
    - Total Revenue: {m['total_revenue']:,.0f} SAR
    - Net Profit: {m['total_profit']:,.0f} SAR
    - Average Margin: {m['margin_pct']}%
    - Next Month Forecast: {m['forecast']:,.0f} SAR
    - Top Markets: {list(m['city_dist'].keys())}
    - Highest Margin Products: {m['top_margins']}
    - Lowest Margin Products: {m['bot_margins']}
    Answer strictly based on this context. Keep it professional and insightful.
    """
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "system", "content": ctx}, {"role": "user", "content": query}])
        return res.choices[0].message.content
    except Exception as e: return f"Connection Error: {e}"
