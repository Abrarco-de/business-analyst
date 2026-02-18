import pandas as pd
import streamlit as st
from groq import Groq
# NEW IMPORT FOR 2026
try:
    from mistralai import Mistral
except ImportError:
    st.error("Missing Library: Run 'pip install mistralai' and restart the app.")

# 1. ENGINE CONFIG
def configure_dual_engines(groq_key, mistral_key):
    try:
        g = Groq(api_key=groq_key)
        # 2026 SDK uses Mistral(api_key=...)
        m = Mistral(api_key=mistral_key)
        return g, m
    except Exception as e:
        st.error(f"Config Error: {e}")
        return None, None

# 2. DATA CLEANER (Groq)
def process_business_data(groq_client, df):
    df.columns = [str(c).strip() for c in df.columns]
    
    # Simple, fast logic to find SAR values
    r_col = next((c for c in df.columns if any(x in c.lower() for x in ['rev', 'sale', 'amount'])), df.columns[0])
    p_col = next((c for c in df.columns if 'prof' in c.lower()), None)
    
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col else df['_rev'] * 0.20
    
    m = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "margin": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0,
        "vat": round(df['_rev'].sum() * 0.15, 2)
    }
    return m, df

# 3. STRATEGIST (Mistral)
def get_ai_response(mistral_client, metrics, df, user_query):
    try:
        # Use the 2026 'chat.complete' method
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{
                "role": "user", 
                "content": f"SME Data: {metrics}. Question: {user_query}. Provide a Saudi business strategy tip."
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Insight Error: {str(e)}"
