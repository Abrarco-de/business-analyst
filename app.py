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
        conf_score = 0
        
        # 1. Map Columns
        rev_col = detect_col(df, ['Sales', 'Revenue', 'Amount'])
        prof_col = detect_col(df, ['Profit', 'Margin'])
        date_col = detect_col(df, ['Date', 'Order Date'])
        qty_col = detect_col(df, ['Qty', 'Quantity', 'Units'])
        disc_col = detect_col(df, ['Discount', 'Disc'])
        prod_col = detect_col(df, ['Sub Category', 'Product', 'Item']) or df.columns[0]

        # 2. Core Calculations
        if not rev_col: return {"error": "Sales/Revenue column not found."}, df_raw
        df['_rev'] = clean_num(df[rev_col])
        conf_score += 25 # Revenue found
        
        if prof_col:
            df['_prof'] = clean_num(df[prof_col])
            meta['real_profit'] = True
            meta['profit_method'] = "Actual"
            conf_score += 25 # Actual Profit found
        else:
            df['_prof'] = df['_rev'] * 0.20
            meta['profit_method'] = "Estimated (20%)"

        if qty_col:
            df['_qty'] = clean_num(df[qty_col])
            meta['has_qty'] = True
            conf_score += 15 # Quantity found
        else:
            df['_qty'] = 0

        # 3. Discount Impact (Calculates how much money was given away)
        if disc_col:
            df['_disc_rate'] = clean_num(df[disc_col])
            # If Sales is $88 and Discount is 0.12, Original was $100. Loss is $12.
            # Formula: Sales * (Disc / (1 - Disc))
            df['_disc_amt'] = df.apply(lambda x: x['_rev'] * (x['_disc_rate']/(1-x['_disc_rate'])) if x['_disc_rate'] < 1 else 0, axis=1)
            conf_score += 15 # Discount data found
        else:
            df['_disc_amt'] = 0

        # 4. Date & Confidence
        trend_dict = {}
        if date_col:
            df['_date'] = pd.to_datetime(df[date_col], errors='coerce')
            if not df['_date'].isna().all():
                meta['has_date'] = True
                conf_score += 20 # Valid dates found
                monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('ME').sum()
                trend_dict = {k.strftime('%Y-%m-%d'): float(v) for k, v in monthly.items()}

        # 5. Product Performance & Logic
        df['_prod'] = df[prod_col].astype(str)
        stats = df.groupby('_prod').agg({'_rev':'sum', '_prof':'sum', '_qty':'sum'})
        stats['margin'] = (stats['_prof'] / stats['_rev'] * 100).fillna(0)
        
        # High-Sales, Low-Margin logic (Items making lots of work but little profit)
        avg_sales = stats['_rev'].mean()
        high_vol_low_m = stats[(stats['_rev'] > avg_sales) & (stats['margin'] < 25)].index.tolist()
        
        top_m = stats.sort_values('margin', ascending=False).head(5)
        bot_m = stats.sort_values('margin', ascending=True).head(5)

        # 6. Final Metric Dictionary
        metrics = {
            "status": "success",
            "meta": meta,
            "conf_score": conf_score,
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "margin_pct": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0,
            "vat_due": float(df['_rev'].sum() * 0.15),
            "avg_order_val": float(df['_rev'].mean()),
            "total_units": int(df['_qty'].sum()) if meta['has_qty'] else None,
            "rev_per_unit": round(df['_rev'].sum() / df['_qty'].sum(), 2) if meta['has_qty'] and df['_qty'].sum() > 0 else None,
            "discount_impact": float(df['_disc_amt'].sum()),
            "bot_margin_list": [f"{n} ({m:.1f}%)" for n, m in bot_m['margin'].items()],
            "top_margin_list": [f"{n} ({m:.1f}%)" for n, m in top_m['margin'].items()],
            "high_vol_low_margin": high_vol_low_m[:5],
            "trend_data": trend_dict
        }
        return metrics, df
    except Exception as e:
        return {"error": str(e)}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI not connected."
    ctx = f"Rev: {m.get('total_revenue')}, Profit: {m.get('total_profit')}. Margin: {m.get('margin_pct')}%. Discount Loss: {m.get('discount_impact')}."
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role":"user", "content":f"{ctx}\nQuestion: {query}"}])
        return res.choices[0].message.content
    except: return "AI logic is currently busy."
