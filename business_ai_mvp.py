import pandas as pd
import streamlit as st
from groq import Groq
try:
    from mistralai import Mistral
except ImportError:
    st.error("Missing Library: Run 'pip install mistralai' and restart the app.")

# 1. ENGINE CONFIG (Updated for 2026 SDK)
def configure_dual_engines(groq_key, mistral_key):
    try:
        g = Groq(api_key=groq_key)
        m = Mistral(api_key=mistral_key)
        return g, m
    except Exception as e:
        return None, None

# 2. THE CLEANER & DATA EXCHANGER (Groq)
def process_business_data(groq_client, df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    
    # Identify key columns
    r_col = next((c for c in df.columns if any(x in c.lower() for x in ['rev', 'sale', 'amount'])), df.columns[0])
    p_col = next((c for c in df.columns if any(x in c.lower() for x in ['prof', 'net'])), None)
    prod_col = next((c for c in df.columns if any(x in c.lower() for x in ['prod', 'item', 'desc'])), df.columns[0])

    # Convert to numbers
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col else df['_rev'] * 0.20
    
    # --- DATA EXCHANGE: Top Products Calculation ---
    top_prods_df = df.groupby(prod_col)['_prof'].sum().sort_values(ascending=False).head(3)
    best_product_info = ", ".join([f"{name} ({val:,.0f} SAR)" for name, val in top_prods_df.items()])

    m = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "margin": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0,
        "best_product": best_product_info,
        "vat": round(df['_rev'].sum() * 0.15, 2)
    }
    return m, df

# 3. THE STRATEGIST (Mistral)
def get_ai_response(mistral_client, metrics, user_query):
    try:
        # We pass the 'best_product' calculation directly to Mistral's brain
        prompt = f"""
        CONTEXT: Saudi SME. Revenue: {metrics['rev']} SAR. Profit: {metrics['prof']} SAR.
        TOP PROFIT PRODUCTS: {metrics['best_product']}
        
        USER: {user_query}
        
        INSTRUCTIONS: 
        1. Be extremely brief (max 3 sentences).
        2. If asked about best products, use the data above.
        3. Do NOT provide a summary unless asked.
        """
        
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Insight Error: {str(e)}"
