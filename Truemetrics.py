import pandas as pd
import numpy as np
from mistralai import Mistral
import logging

logging.basicConfig(level=logging.INFO)

DEFAULT_MARGIN = 0.20

def get_mistral_client(api_key):
    try:
        if api_key: return Mistral(api_key=api_key)
    except Exception as e:
        logging.error(f"Mistral Init Error: {e}")
    return None

def clean_num(series):
    # Handles currency symbols and commas
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
            res["error"] = "No data found."
            return res, None

        df = df_raw.copy()
        detect_map = {
            'Revenue': ['sales', 'revenue', 'amount', 'total', 'price'],
            'Profit': ['profit', 'margin', 'net'],
            'Date': ['date', 'time', 'day'],
            'Item': ['item', 'product', 'category', 'description']
        }
        
        found = {k: detect_col(df, v) for k, v in detect_map.items()}
        if not found['Revenue']:
            res["error"] = "Revenue column not found."
            return res, df

        # Math logic
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
        res["error"] = "Data processing failed."
        return res, df_raw

def get_consultant_insight(client, metrics, is_paid=False):
    if not client: return "Mistral Consultant Offline."
    
    # Instructions to force a human-level conversation
    prompt = f"""
    You are a Senior Business Consultant for small retail shops in Saudi Arabia. 
    Analyze these metrics: Revenue {metrics['total_revenue']:,} SAR, Orders {metrics['orders']}, AOV {metrics['aov']:.2f} SAR, Margin {metrics['margin']:.1f}%, Top Products: {metrics['top_items']}.
    
    Structure your response as a personal letter to the owner:
    1. Start with a warm professional greeting (e.g., Ahlan).
    2. Give a 2-sentence summary of how their business is 'feeling' right now (energetic, stable, or struggling).
    3. Identify ONE specific trend (e.g., 'Your average basket size is high, meaning customers trust your selection').
    4. End with ONE clear, bold action to take today.
    
    Tone: Sophisticated but simple. No bullet points. No technical jargon. Make it feel like a WhatsApp message from a mentor.
    """
    
    try:
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"The consultant is gathering thoughts... (Error: {e})"
