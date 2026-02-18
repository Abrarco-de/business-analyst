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
            # Matches exact or partial (e.g., "Total Sales" matches "Sales")
            if k.lower() == c.lower() or k.lower() in c.lower():
                return c
    return None

def process_business_data(df_raw):
    try:
        if df_raw is None or df_raw.empty:
            return {"error": "The uploaded file is empty."}, None
            
        df = df_raw.copy()
        
        # 1. AGGRESSIVE COLUMN DETECTION
        # Added Amount, Price, Total, Income, and Arabic المبيعات
        rev_col = detect_col(df, ['Sales', 'Revenue', 'Amount', 'Total', 'Price', 'Income', 'المبيعات', 'البيع'])
        
        # Added Profit, Margin, Earnings, and Arabic الربح
        prof_col = detect_col(df, ['Profit', 'Margin', 'Earnings', 'Net', 'Gain', 'الربح', 'صافي'])
        
        date_col = detect_col(df, ['Date', 'Time', 'Year', 'Month', 'Period', 'التاريخ'])
        cat_col = detect_col(df, ['Category', 'Dept', 'Group', 'Type', 'الفئة'])
        sub_cat_col = detect_col(df, ['Sub Category', 'Product', 'Item', 'Description', 'المنتج'])
        city_col = detect_col(df, ['City', 'Region', 'Location', 'Branch', 'Area', 'المدينة'])
        qty_col = detect_col(df, ['Qty', 'Quantity', 'Units', 'Count', 'Sold', 'الكمية']) 

        if not rev_col:
            found_cols = ", ".join(df.columns.tolist())
            return {"error": f"TrueMetrics could not find a Sales/Revenue column. Found columns: [{found_cols}]"}, df_raw

        # 2. Cleaning
        df['_rev'] = clean_num(df[rev_col])
        df['_prof'] = clean_num(df[prof_col]) if prof_col else df['_rev'] * 0.20
        df['_qty'] = clean_num(df[qty_col]) if qty_col else 1 

        # 3. Aggregations for AI
        # Fallback to the first column if category/city aren't found
        cat_key = cat_col if cat_col else df.columns[0]
        city_key = city_col if city_col else (cat_col if cat_col else df.columns[0])

        profile = {
            "categories": df.groupby(cat_key)['_rev'].sum().to_dict(),
            "cities": df.groupby(city_key)['_rev'].sum().to_dict(),
            "sub_cat_units": df.groupby(sub_cat_col or cat_key).size().to_dict()
        }

        # 4. Trend Logic
        trend_dict = {}
        if date_col:
            df['_date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            if not df['_date'].isna().all():
                try: 
                    monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('ME').sum()
                except: 
                    monthly = df.dropna(subset=['_date']).set_index('_date')['_rev'].resample('M').sum()
                trend_dict = {k.strftime('%Y-%m-%d'): float(v) for k, v in monthly.items()}

        p_stats = df.groupby(sub_cat_col or cat_key).agg({'_rev':'sum', '_prof':'sum'})
        p_stats['m'] = (p_stats['_prof']/p_stats['_rev']*100).fillna(0)

        metrics = {
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "total_units": int(df['_qty'].sum()),
            "vat_due": float(df['_rev'].sum() * 0.15),
            "margin_pct": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "bot_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m').head(3)['m'].items()],
            "top_margin_list": [f"{n} ({m:.1f}%)" for n, m in p_stats.sort_values('m', ascending=False).head(3)['m'].items()],
            "trend_data": trend_dict,
            "data_profile": profile 
        }
        return metrics, df
    except Exception as e:
        return {"error": f"Engine Error: {str(e)}"}, df_raw

def get_ai_response(mistral_client, m, query):
    if not mistral_client: return "AI not connected."
    profile = m.get('data_profile', {})
    context = f"""
    You are TrueMetrics AI. 
    Sales: {m['total_revenue']:,} SAR | Profit: {m['total_profit']:,} SAR | VAT: {m['vat_due']:,} SAR | Units: {m['total_units']:,}.
    Details: {profile}
    """
    try:
        res = mistral_client.chat.complete(model="mistral-large-latest", messages=[{"role":"user", "content": f"{context}\nQuestion: {query}"}])
        return res.choices[0].message.content
    except: return "Analysing..."
