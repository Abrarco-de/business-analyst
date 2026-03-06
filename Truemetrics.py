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
    if series is None: return pd.Series(dtype=float)
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords):
    cols = [str(c).strip() for c in df.columns]
    for k in keywords:
        for c in cols:
            if k.lower() in c.lower(): return c
    return None

def process_business_data(df_raw):
    # DEFINING THE SKELETON: Ensures the UI ALWAYS receives these keys, preventing crashes
    res = {
        "error": None, "warning": None, "mapping_preview": [], "confidence": 0,
        "total_revenue": 0.0, "total_profit": 0.0, "margin_pct": 0.0, "forecast": 0.0,
        "units": len(df_raw) if df_raw is not None else 0, "loc_header": "Segment",
        "city_dist": {}, "bot_margins": [], "top_margins": [], "trend_data": {}
    }
    
    try:
        if df_raw is None or df_raw.empty:
            res["error"] = "The uploaded dataset is empty."
            return res, None

        df = df_raw.copy()
        
        # UNIVERSAL MAP
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price', 'income', 'weekly', 'المبيعات'],
            'Profit': ['profit', 'margin', 'earnings', 'net', 'gain', 'الربح'],
            'Date': ['date', 'time', 'year', 'month', 'period', 'التاريخ'],
            'Category': ['category', 'dept', 'group', 'type', 'item', 'product', 'الفئة'],
            'Location': ['city', 'region', 'location', 'branch', 'store', 'المدينة']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        
        # Confidence logic
        found_count = sum(1 for v in found.values() if v)
        res["confidence"] = int((found_count / len(detect_map)) * 100)
        
        for k, v in found.items():
            if v: res["mapping_preview"].append({"Role": k, "Detected Header": v})

        # SAFE REVENUE EXTRACTION
        if not found['Revenue']:
            # Fallback: Try to find any numeric column if "Sales" isn't found
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                found['Revenue'] = num_cols[0]
                res["warning"] = f"Could not detect a clear Revenue column. Using '{num_cols[0]}' as fallback."
            else:
                res["error"] = "Not sufficient numeric data found to analyze."
                return res, df

        # CORE KPIs
        df['_rev'] = clean_num(df[found['Revenue']])
        if found['Profit']: df['_prof'] = clean_num(df[found['Profit']])
        else: df['_prof'] = df['_rev'] * 0.20 # Default 20% margin estimation
        
        res["total_revenue"] = float(df['_rev'].sum())
        res["total_profit"] = float(df['_prof'].sum())
        if res["total_revenue"] > 0:
            res["margin_pct"] = round((res["total_profit"] / res["total_revenue"]) * 100, 1)

        # SAFE GROUPING (Top/Bottom Performers)
        loc_col = found['Location'] if found['Location'] else found['Category']
        if loc_col:
            res["loc_header"] = str(loc_col)
            # Fill NaNs to prevent grouping crashes
            df[loc_col] = df[loc_col].fillna("Unknown Segment").astype(str)
            
            res["city_dist"] = df.groupby(loc_col)['_rev'].sum().nlargest(5).to_dict()
            
            p_stats = df.groupby(loc_col).agg({'_rev':'sum', '_prof':'sum'})
            p_stats = p_stats[p_stats['_rev'] > 0] # Prevent division by zero
            if not p_stats.empty:
                p_stats['m'] = (p_stats['_prof'] / p_stats['_rev'] * 100).fillna(0)
                sorted_m = p_stats.sort_values('m')
                res["bot_margins"] = [f"{n} ({m:.1f}%)" for n, m in sorted_m.head(4)['m'].items()]
                res["top_margins"] = [f"{n} ({m:.1f}%)" for n, m in sorted_m.tail(4).iloc[::-1]['m'].items()] # reverse for descending

        # SAFE TIME SERIES (Trends & Forecasts)
        if found['Date']:
            df['_dt'] = pd.to_datetime(df[found['Date']], dayfirst=True, errors='coerce')
            valid_dt = df.dropna(subset=['_dt']).copy()
            if not valid_dt.empty:
                valid_dt = valid_dt.sort_values('_dt')
                valid_dt['Month_Year'] = valid_dt['_dt'].dt.strftime('%Y-%m')
                monthly_sum = valid_dt.groupby('Month_Year')['_rev'].sum().sort_index()
                res["trend_data"] = {pd.to_datetime(k).strftime('%b %Y'): float(v) for k, v in monthly_sum.items()}
                
                # Forecasting
                if len(monthly_sum) >= 3: res["forecast"] = float(monthly_sum.iloc[-3:].mean())
                elif len(monthly_sum) > 0: res["forecast"] = float(monthly_sum.mean())

        return res, df
    except Exception as e:
        res["error"] = f"Fatal Engine Error: {str(e)}. Attempting to recover."
        return res, df_raw

def get_ai_response(mistral_client, m, query, is_paid=False):
    if not mistral_client: return "AI Consultant Offline. Check API connection."
    tier_msg = "You are a senior data expert consulting a premium client. Be highly strategic." if is_paid else "You are a basic AI. Answer briefly."
    payload = f"{tier_msg}\nData context: Rev {m['total_revenue']}, Margin {m['margin_pct']}%, Best Segments {m['top_margins']}."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "system", "content": payload}, {"role": "user", "content": query}])
        return res.choices[0].message.content
    except Exception as e: return f"AI Error: {str(e)}"
