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
        
        # Meta Info & Confidence Score Calculation
        found_count = 0
        for k, v in found.items():
            if v: 
                mapping_details.append({"AI Concept": k, "Your Column": v})
                found_count += 1
        
        confidence_score = int((found_count / len(detect_map)) * 100)

        if not found['Revenue']: return {"error": "Missing Sales Column"}, df_raw

        # Core Math
        df['_rev'] = clean_num(df[found['Revenue']])
        df['_prof'] = clean_num(df[found['Profit']]) if found['Profit'] else df['_rev'] * 0.20
        
        city_key = found['City'] if found['City'] else None
        city_dist = df.groupby(by=city_key)['_rev'].sum().nlargest(6).to_dict() if city_key else {}
        
        prod_key = found['Product'] if found['Product'] else df.columns[0]
        p_stats = df.groupby(by=prod_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).replace([np.inf, -np.inf], 0).fillna(0)

        # Trend & Forecast
        trend_dict = {}
        forecast_val = 0
        if found['Date']:
            df['_dt'] = pd.to_datetime(df[found['Date']], dayfirst=True, errors='coerce')
            temp_df = df.dropna(subset=['_dt']).copy()
            if not temp_df.empty:
                temp_df['Month_Year'] = temp_df['_dt'].dt.strftime('%Y-%m')
                monthly_sum = temp_df.groupby('Month_Year')['_rev'].sum().sort_index()
                trend_dict = {pd.to_datetime(k).strftime('%b %Y'): float(v) for k, v in monthly_sum.items()}
                
                if len(monthly_sum) >= 3: forecast_val = monthly_sum.iloc[-3:].mean()
                elif len(monthly_sum) > 0: forecast_val = monthly_sum.iloc[-1]

        return {
            "mapping_preview": mapping_details,
            "confidence": confidence_score,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "forecast": float(forecast_val),
            "units": len(df),
            "city_dist": city_dist,
            "bot_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(4)['m'].items()],
            "top_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(4)['m'].items()],
            "trend_data": trend_dict
        }, df
    except Exception as e: return {"error": f"Engine Logic Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI Engine Offline. Check API keys."
    ctx = f"Data Summary: Revenue {m['total_revenue']} SAR, Margin {m['margin_pct']}%, Records {m['units']}."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "system", "content": ctx}, {"role": "user", "content": query}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {e}"
