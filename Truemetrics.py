import pandas as pd
import numpy as np
from groq import Groq
from mistralai import Mistral
import logging

# 10. Add Basic Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 11. Minor Code Style Improvements
DEFAULT_MARGIN = 0.20
MAX_ROWS = 200000

def configure_dual_engines(groq_key, mistral_key):
    g, m = None, None
    try:
        if groq_key: g = Groq(api_key=groq_key)
        if mistral_key: m = Mistral(api_key=mistral_key)
    except Exception as e:
        # 1. Avoid Silent Exception Handling
        logging.error(f"Engine configuration error: {e}")
    return g, m

def clean_num(series):
    if series is None: return pd.Series(dtype=float)
    # 4. Improve Numeric Cleaning (Handles commas)
    clean = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(r'[^\d.-]', '', regex=True)
    )
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords):
    # 2. Cache Column Detection (Performance Boost)
    cols = [str(c).strip() for c in df.columns]
    cols_lower = [c.lower() for c in cols]

    for k in keywords:
        k = k.lower()
        for i, c in enumerate(cols_lower):
            if k in c:
                return cols[i]
    return None

def process_business_data(df_raw):
    logging.info("Processing dataset started.")
    res = {
        "error": None, "warning": None, "mapping_preview": [], "confidence": 0,
        "total_revenue": 0.0, "total_profit": 0.0, "margin_pct": 0.0, "forecast": 0.0,
        "units": 0, "loc_header": "Segment", "orders": 0, "avg_order_value": 0.0,
        "city_dist": {}, "bot_margins": [], "top_margins": [], "trend_data": {}
    }
    
    try:
        if df_raw is None or df_raw.empty:
            res["error"] = "The uploaded dataset is empty."
            return res, None

        # 3. Limit Dataset Size (Stability protection)
        if len(df_raw) > MAX_ROWS:
            res["warning"] = f"Dataset truncated to {MAX_ROWS:,} rows to maintain system stability."
            df_raw = df_raw.head(MAX_ROWS)
            
        res["units"] = len(df_raw)
        df = df_raw.copy()
        
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price', 'income', 'weekly', 'المبيعات'],
            'Profit': ['profit', 'margin', 'earnings', 'net', 'gain', 'الربح'],
            'Date': ['date', 'time', 'year', 'month', 'period', 'التاريخ'],
            'Category': ['category', 'dept', 'group', 'type', 'item', 'product', 'الفئة'],
            'Location': ['city', 'region', 'location', 'branch', 'store', 'المدينة']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        found_count = sum(1 for v in found.values() if v)
        res["confidence"] = int((found_count / len(detect_map)) * 100)
        
        for k, v in found.items():
            if v: res["mapping_preview"].append({"Role": k, "Detected Header": v})

        if not found['Revenue']:
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                found['Revenue'] = num_cols[0]
                warn_msg = f"No Revenue column detected. Falling back to '{num_cols[0]}'."
                res["warning"] = f"{res['warning']} | {warn_msg}" if res['warning'] else warn_msg
            else:
                res["error"] = "Not sufficient numeric data found to analyze."
                return res, df

        # 6. Ensure Revenue Cannot Be Negative (Refund protection)
        df['_rev'] = clean_num(df[found['Revenue']]).clip(lower=0)
        
        if found['Profit']: df['_prof'] = clean_num(df[found['Profit']])
        else: df['_prof'] = df['_rev'] * DEFAULT_MARGIN # Using constant
        
        # 7. Add Order Count & AOV Metric
        res["orders"] = int((df['_rev'] > 0).sum())
        res["total_revenue"] = float(df['_rev'].sum())
        res["total_profit"] = float(df['_prof'].sum())
        
        if res["orders"] > 0:
            res["avg_order_value"] = res["total_revenue"] / res["orders"]
            
        if res["total_revenue"] > 0:
            res["margin_pct"] = round((res["total_profit"] / res["total_revenue"]) * 100, 1)

        loc_col = found['Location'] if found['Location'] else found['Category']
        
        # 12. Protect Against Missing Columns During Grouping
        if loc_col and loc_col in df.columns:
            res["loc_header"] = str(loc_col)
            df[loc_col] = df[loc_col].fillna("Unknown").astype(str)
            res["city_dist"] = df.groupby(loc_col)['_rev'].sum().nlargest(5).to_dict()
            
            p_stats = df.groupby(loc_col).agg({'_rev':'sum', '_prof':'sum'})
            p_stats = p_stats[p_stats['_rev'] > 0]
            if not p_stats.empty:
                p_stats['m'] = (p_stats['_prof'] / p_stats['_rev'] * 100).fillna(0)
                sorted_m = p_stats.sort_values('m')
                res["bot_margins"] = [f"{n} ({m:.1f}%)" for n, m in sorted_m.head(4)['m'].items()]
                res["top_margins"] = [f"{n} ({m:.1f}%)" for n, m in sorted_m.tail(4).iloc[::-1]['m'].items()]

        # 5. Protect Date Parsing
        if found['Date'] and found['Date'] in df.columns:
            try:
                df['_dt'] = pd.to_datetime(df[found['Date']], errors='coerce')
            except Exception as e:
                logging.error(f"Date parsing failed: {e}")
                df['_dt'] = pd.NaT

            valid_dt = df.dropna(subset=['_dt']).copy()
            if not valid_dt.empty:
                valid_dt = valid_dt.sort_values('_dt')
                valid_dt['Month_Year'] = valid_dt['_dt'].dt.strftime('%Y-%m')
                monthly_sum = valid_dt.groupby('Month_Year')['_rev'].sum().sort_index()
                res["trend_data"] = {pd.to_datetime(k).strftime('%b %Y'): float(v) for k, v in monthly_sum.items()}
                
                # 8. Improve Forecast Logic (Median stability)
                if len(monthly_sum) >= 3: 
                    recent = monthly_sum.tail(3)
                    res["forecast"] = float(recent.median())
                elif len(monthly_sum) > 0: 
                    res["forecast"] = float(monthly_sum.mean())

        logging.info("Processing completed successfully.")
        return res, df
    except Exception as e:
        logging.error(f"Fatal Engine Error: {e}")
        res["error"] = "System encountered an unexpected error processing this file layout."
        return res, df_raw

def get_ai_response(mistral_client, m, query, is_paid=False):
    if not mistral_client: return "AI Consultant Offline. Check API connection."
    
    tier_msg = "You are a senior data expert consulting a premium retail client. Provide strategic advice." if is_paid else "You are a basic AI assistant. Answer briefly."
    
    # 9. Improve AI Prompt Context
    payload = f"""
    {tier_msg}
    Here is the exact data context for the current business:
    - Total Revenue: {m.get('total_revenue', 0):,.2f} SAR
    - Profit Margin: {m.get('margin_pct', 0)}%
    - Total Valid Orders: {m.get('orders', 0):,}
    - Average Order Value (AOV): {m.get('avg_order_value', 0):,.2f} SAR
    - Top Performers: {m.get('top_margins', [])}
    - Risk Segments (Low Margin): {m.get('bot_margins', [])}
    - Next Month Forecast (Median): {m.get('forecast', 0):,.2f} SAR
    
    Provide your advice based strictly on this context.
    """
    
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role": "system", "content": payload}, {"role": "user", "content": query}])
        return res.choices[0].message.content
    except Exception as e: 
        logging.error(f"AI API Error: {e}")
        return f"AI communication error: Try again."
