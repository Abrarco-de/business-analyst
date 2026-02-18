import pandas as pd
import google.generativeai as genai
from groq import Groq
import streamlit as st

# --- 1. CONFIGURATION ---
def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except: return None

# --- 2. CALCULATE ADVANCED SME METRICS ---
def calculate_precise_metrics(df):
    # Clean column names
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    cols = [c.lower() for c in df.columns]

    # Smart column detection
    r_col = next((c for c in df.columns if 'sale' in c.lower() or 'revenue' in c.lower() or 'amount' in c.lower()), df.columns[0])
    p_col = next((c for c in df.columns if 'profit' in c.lower() or 'margin' in c.lower()), None)
    prod_col = next((c for c in df.columns if 'product' in c.lower() or 'item' in c.lower() or 'category' in c.lower()), df.columns[0])

    # Convert to numeric
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    if p_col:
        df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    else:
        df['_prof'] = df['_rev'] * 0.25 # Assume 25% margin if not provided

    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()

    m = {
        "rev": round(total_rev, 2),
        "prof": round(total_prof, 2),
        "vat": round(total_rev * 0.15, 2), # Saudi VAT 15%
        "margin": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "best_seller": str(df.groupby(prod_col)['_rev'].sum().idxmax()) if total_rev > 0 else "N/A"
    }
    return m, df

# --- 3. SWAPPED INTELLIGENCE BRIDGE ---
def get_intelligent_answer(groq_client, df, user_query, m):
    try:
        # ROLE 1: Groq (Data Researcher) - High-speed data scanning
        data_summary = df.head(100).to_string()
        research_prompt = f"""
        Analyze this data for query: {user_query}
        Stats: Rev {m['rev']} SAR, Profit {m['prof']} SAR.
        Data Sample:
        {data_summary}
        Return a 'Fact Sheet' with specific numbers and trends.
        """
        
        research = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}]
        )
        fact_sheet = research.choices[0].message.content

        # ROLE 2: Gemini (Executive Consultant) - High-level Saudi SME strategy
        # Using the current 2026 stable model name
        model = genai.GenerativeModel('gemini-3-flash') 
        
        consultant_prompt = f"""
        Fact Sheet: {fact_sheet}
        Business Context: Total Revenue {m['rev']} SAR, Profit Margin {m['margin']}%.
        Question: {user_query}
        
        Provide a concise, strategic answer. Mention SAR values and one actionable tip.
        """
        response = model.generate_content(consultant_prompt)
        return response.text

    except Exception as e:
        return f"System Error: {str(e)}"
