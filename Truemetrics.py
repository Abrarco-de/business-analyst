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
        
        # UNIVERSAL DETECTION MAP (Covers most business files)
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price', 'income', 'weekly', 'المبيعات'],
            'Profit': ['profit', 'margin', 'earnings', 'net', 'gain', 'الربح'],
            'Date': ['date', 'time', 'year', 'month', 'period', 'التاريخ'],
            'Category': ['category', 'dept', 'group', 'type', 'item', 'product', 'الفئة'],
            'Location': ['city', 'region', 'location', 'branch', 'store', 'المدينة']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        
        # Confidence logic: Did we find the basics?
        essential_keys = ['Revenue', 'Date']
        found_essentials = sum(1 for k in essential_keys if found[k])
        confidence_score = int((found_essentials / len(essential_keys)) * 100) if found['Revenue'] else 0
        
        for k, v in found.items():
            if v: mapping_details.append({"Role": k, "Detected Header": v})

        if not found['Revenue']:
            return {"error": "Universal Engine Error: Could not identify a Sales or Revenue column. Please rename your main column to 'Sales'."}, df_raw

        # MATH LOGIC
        rev_col = found['Revenue']
        df['_rev'] = clean_num(df[rev_col])
        df['_prof'] = clean_num(df[found['Profit']]) if found['Profit'] else df['_rev'] * 0.20
        
        # Grouping Logic (Falls back to first column if Location isn't found)
        loc_key = found['Location'] if found['Location'] else (found['Category'] if found['Category'] else df.columns[0])
        loc_dist = df.groupby(by=loc_key)['_rev'].sum().nlargest(5).to_dict()
        
        # Margin Analysis
        p_stats = df.groupby(by=loc_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).replace([np.inf, -np.inf], 0).fillna(0)

        # Time Series
        trend_dict = {}
        forecast_val = 0
        if found['Date']:
            df['_dt'] = pd.to_datetime(df[found['Date']], dayfirst=True, errors='coerce')
            temp_df = df.dropna(subset=['_dt']).copy()
            if not temp_df.empty:
                temp_df = temp_df.sort_values('_dt')
                temp_df['Month_Year'] = temp_df['_dt'].dt.strftime('%Y-%m')
                monthly_sum = temp_df.groupby('Month_Year')['_rev'].sum().sort_index()
                trend_dict = {pd.to_datetime(k).strftime('%b %Y'): float(v) for k, v in monthly_sum.items()}
                forecast_val = monthly_sum.mean() if not monthly_sum.empty else 0

        return {
            "mapping_preview": mapping_details,
            "confidence": confidence_score,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() != 0 else 0,
            "forecast": float(forecast_val),
            "units": len(df),
            "loc_header": loc_key,
            "city_dist": loc_dist,
            "bot_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(4)['m'].items()],
            "top_margins": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(4)['m'].items()],
            "trend_data": trend_dict
        }, df
    except Exception as e: return {"error": f"General Engine Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI Consultant Offline."
    
    # The Payload is now Universal
    payload = f"""
    You are an AI Data Scientist. Here is the analysis of the uploaded file:
    - Total Revenue: {m['total_revenue']:,.2f}
    - Profitability: {m['margin_pct']}%
    - Top Segments (based on {m['loc_header']}): {list(m['city_dist'].keys())}
    - Trend Points: {len(m['trend_data'])} months detected.
    - Highest Performing: {m['top_margins']}
    - Lowest Performing: {m['bot_margins']}
    Answer strictly using these values.
    """
    
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "system", "content": payload}, {"role": "user", "content": query}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {str(e)}"
