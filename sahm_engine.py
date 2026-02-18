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
            if k.lower() == c.lower() or k.lower() in c.lower():
                return c
    return None

def process_business_data(df_raw):
    try:
        df = df_raw.copy()
        
        # Mapping
        rev_col = detect_col(df, ['Sales', 'Revenue'])
        prof_col = detect_col(df, ['Profit'])
        city_col = detect_col(df, ['City'])
        cat_col = detect_col(df, ['Category', 'Sub Category'])

        df['_rev'] = clean_num(df[rev_col])
        df['_prof'] = clean_num(df[prof_col])
        vat_rate = 0.15
        
        # AI Context Mapping
        profile = {
            "top_cities": df.groupby(city_col)['_rev'].sum().nlargest(3).to_dict() if city_col else {},
            "top_cats": df.groupby(cat_col)['_rev'].sum().nlargest(3).to_dict() if cat_col else {}
        }

        metrics = {
            "total_revenue": float(df['_rev'].sum()),
            "total_profit": float(df['_prof'].sum()),
            "vat_due": float(df['_rev'].sum() * vat_rate),
            "margin": round((df['_prof'].sum()/df['_rev'].sum()*100), 1) if df['_rev'].sum() > 0 else 0,
            "units": len(df),
            "data_profile": profile
        }
        return metrics
    except Exception as e:
        return {"error": str(e)}

def get_ai_response(client, m, query):
    if not client: return "AI not linked."
    
    # Ensuring VAT and details are in the AI's "brain"
    context = f"""
    System: You are Sahm BI, a Saudi Business Consultant.
    Data: Sales {m['total_revenue']:,} SAR, VAT {m['vat_due']:,} SAR, Profit {m['total_profit']:,} SAR, Margin {m['margin']}%.
    Breakdown: {m['data_profile']}
    """
    try:
        res = client.chat.complete(model="mistral-large-latest", 
                                   messages=[{"role":"user", "content": f"{context}\nUser: {query}"}])
        return res.choices[0].message.content
    except: return "I'm analyzing the data, please try again."
