import pandas as pd
import numpy as np
from mistralai import Mistral
import logging

# Basic logging for debugging
logging.basicConfig(level=logging.INFO)

DEFAULT_MARGIN = 0.20

def get_mistral_client(api_key):
    try:
        if api_key:
            return Mistral(api_key=api_key)
    except Exception as e:
        logging.error(f"Mistral Init Error: {e}")
    return None

def clean_num(series):
    # Handles currency symbols, commas, and non-numeric junk
    clean = series.astype(str).str.replace(",", "", regex=False).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0)

def detect_col(df, keywords):
    cols = [str(c).strip() for c in df.columns]
    cols_lower = [c.lower() for c in cols]
    for k in keywords:
        k = k.lower()
        for i, c in enumerate(cols_lower):
            if k in c: return cols[i]
    return None

def process_business_data(df_raw):
    res = {"error": None, "raw_metrics": {}}
    try:
        if df_raw is None or df_raw.empty:
            res["error"] = "The uploaded file appears to be empty."
            return res, None

        df = df_raw.copy()
        
        # Mapping logic
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price', 'المبيعات'],
            'Profit': ['profit', 'margin', 'net', 'الربح'],
            'Item': ['item', 'product', 'category', 'description', 'الفئة']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        
        if not found['Revenue']:
            res["error"] = "We couldn't identify a 'Sales' or 'Revenue' column in your file."
            return res, df

        # Core Analytics
        df['_rev'] = clean_num(df[found['Revenue']]).clip(lower=0)
        df['_prof'] = clean_num(df[found['Profit']]) if found['Profit'] else df['_rev'] * DEFAULT_MARGIN
        
        total_rev = df['_rev'].sum()
        total_prof = df['_prof'].sum()
        margin = (total_prof / total_rev * 100) if total_rev > 0 else 0
        orders = int((df['_rev'] > 0).sum())
        aov = total_rev / orders if orders > 0 else 0

        # Item analysis
        item_col = found['Item']
        top_items = []
        if item_col:
            top_items = df.groupby(item_col)['_rev'].sum().nlargest(3).index.tolist()

        res["raw_metrics"] = {
            "total_revenue": total_rev,
            "orders": orders,
            "aov": aov,
            "margin": margin,
            "top_items": top_items
        }
        
        return res, df
    except Exception as e:
        logging.error(f"Engine Error: {e}")
        res["error"] = "Something went wrong while reading the data structure."
        return res, df_raw

def get_consultant_insight(m_client, metrics):
    if not m_client:
        return "The Consultant's AI connection is missing. Please check your API key."
    
    prompt = f"""
    Context: You are a high-level Retail Consultant for a shop in Saudi Arabia. 
    Metrics: Revenue {metrics['total_revenue']:,} SAR, Orders {metrics['orders']}, AOV {metrics['aov']:.2f} SAR, Margin {metrics['margin']:.1f}%, Top Products: {metrics['top_items']}.
    
    Task: Write a short, human-level briefing for the shop owner. 
    1. Start with a warm, professional greeting.
    2. Explain the 'vibe' of their business based on these numbers. 
    3. Identify one specific insight (e.g., talk about their AOV or their top items).
    4. Give one clear, actionable advice for today.
    
    Style: Strategic, empathetic, and professional. No bullet points. Just 2-3 short, clean paragraphs.
    """
    
    try:
        response = m_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Your consultant is reviewing the data but encountered an AI error: {e}"
