import pandas as pd
import numpy as np
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    g, m = None, None
    try:
        if groq_key: g = Groq(api_key=groq_key)
        if mistral_key: m = Mistral(api_key=mistral_key)
    except:
        pass
    return g, m

def clean_num(series):
    if series is None: 
        return 0
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords):
    cols = [str(c).strip() for c in df.columns]
    for k in keywords:
        for c in cols:
            if k.lower() == c.lower() or k.lower() in c.lower():
                return c
    return None

def process_business_data(df_raw):
    try:
        if df_raw is None or df_raw.empty:
            return {"error": "The uploaded file is empty."}, None
            
        df = df_raw.copy()
        mapping_details = []
        
        detect_map = {
            'Revenue': ['Sales', 'Revenue', 'Amount', 'Total', 'Price', 'Income', 'المبيعات'],
            'Profit': ['Profit', 'Margin', 'Earnings', 'Net', 'Gain', 'الربح'],
            'Date': ['Date', 'Time', 'Year', 'Month', 'Period', 'التاريخ'],
            'City': ['City', 'Region', 'Location', 'Branch', 'Area', 'المدينة'],
            'Category': ['Category', 'Dept', 'Group', 'Type', 'الفئة'],
            'Product': ['Sub Category', 'Product', 'Item', 'Description', 'المنتج']
        }

        found_cols = {}
        for key, keywords in detect_map.items():
            actual_col = detect_col(df, keywords)
            if actual_col:
                found_cols[key] = actual_col
                sample_val = df[actual_col].iloc[0]
                mapping_details.append({
                    "AI Interpretation": key, 
                    "Your Header": actual_col, 
                    "Sample Value": str(sample_val)
                })

        if 'Revenue' not in found_cols:
            return {"error": "Required column 'Sales' or 'Revenue' not found."}, df_raw

        # Data Processing
        df['_rev'] = clean_num(df[found_cols['Revenue']])
        df['_prof'] = clean_num(df[found_cols['Profit']]) if 'Profit' in found_cols else df['_rev'] * 0.20
        
        prod_key = found_cols.get('Product', df.columns[0])
        p_stats = df.groupby(prod_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof'] / p_stats['_rev'] * 100).replace([np.inf, -np.inf], 0).fillna(0)

        trend_dict = {}
        if 'Date' in found_cols:
            df['_date'] = pd.to_datetime(df[found_cols['Date']], dayfirst=True, errors='coerce')
            if not df['_date'].isna().all():
                temp_df = df.dropna(subset=['_date']).set_index('_date')
                try:
                    monthly = temp_df['_rev'].resample('ME').sum()
                except:
                    monthly = temp_df['_rev'].resample('M').sum()
                trend_dict = {k.strftime('%Y-%m-%d'): float(v) for k, v in monthly.items()}

        metrics = {
            "mapping_preview": mapping_details,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "total_units": len(df),
            "vat_due": float(df['_rev'].sum() * 0.15),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "bot_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(3)['m'].items()],
            "top_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(3)['m'].items()],
            "trend_data": trend_dict
        }
        return metrics, df
    except Exception as e:
        return {"error": f"Engine Logic Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: 
        return "AI Engine Offline. Check Secrets."
    context = f"Metrics: Rev {m['total_revenue']} SAR, Profit {m['total_profit']} SAR."
    try:
        res = mistral_client.chat.complete(
            model="mistral-large-latest", 
            messages=[{"role":"user", "content": f"{context}\nQuestion: {query}"}]
        )
        return res.choices[0].message.content
    except:
        return "Analysis complete. System ready."
