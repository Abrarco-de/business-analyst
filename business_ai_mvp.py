import pandas as pd
import numpy as np
import google.generativeai as genai
from groq import Groq
import json, re, difflib

# --- 1. CONFIGURATION ---
def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except: return None

# --- 2. ADVANCED COLUMN MAPPING ---
SCHEMA_MAP = {
    "product_col": ["Product", "Category", "Item", "Sub Category", "Description"],
    "revenue_col": ["Sales", "Total Amount", "Revenue", "Amount", "Subtotal"],
    "profit_col": ["Profit", "Margin", "Earnings", "Net Profit"],
    "price_col": ["Price", "Unit Price", "Rate"],
    "qty_col": ["Quantity", "Qty", "Count"]
}

def find_best_column(actual_cols, target_key):
    possible_names = SCHEMA_MAP.get(target_key, [])
    for name in possible_names:
        for col in actual_cols:
            if col.lower() == name.lower(): return col
    # Fuzzy Match
    for name in possible_names:
        matches = difflib.get_close_matches(name.lower(), [c.lower() for c in actual_cols], n=1, cutoff=0.8)
        if matches: return next(c for c in actual_cols if c.lower() == matches[0])
    return None

def robust_numeric(df, col_name):
    if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
    clean = df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0.0)

# --- 3. THE INTELLIGENCE BRIDGE (Gemini + Groq) ---
def get_intelligent_answer(groq_client, df, user_query, metrics):
    try:
        # Agent 1: Gemini (The Researcher) scans the full dataframe
        model = genai.GenerativeModel('gemini-1.5-flash')
        research_prompt = f"""
        Analyze this user query: "{user_query}" 
        Based on the columns {list(df.columns)} and a sample of the data:
        {df.head(5).to_string()}
        
        Tasks:
        1. Search the dataset for relevant facts (specific products, dates, or cities mentioned).
        2. Provide specific totals or averages related to the query.
        3. If the query is general, provide a breakdown of the top 3 items.
        Return ONLY a concise Fact Sheet.
        """
        research_response = model.generate_content(research_prompt)
        fact_sheet = research_response.text

        # Agent 2: Groq (The Strategic Consultant)
        analysis = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Saudi Business Consultant. Use the provided Fact Sheet to give a specific, data-backed answer. No generic advice."},
                {"role": "user", "content": f"Fact Sheet: {fact_sheet}\n\nMetrics: Rev {metrics['rev']}, Prof {metrics['prof']}\nQuestion: {user_query}"}
            ],
            temperature=0.2
        )
        return analysis.choices[0].message.content
    except Exception as e:
        return f"AI Bridge Error: {str(e)}"

# --- 4. METRIC CALCULATION ---
def calculate_precise_metrics(df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    cols = df.columns
    
    p_col = find_best_column(cols, "product_col")
    r_col = find_best_column(cols, "revenue_col")
    prof_col = find_best_column(cols, "profit_col")
    pr_col = find_best_column(cols, "price_col")
    q_col = find_best_column(cols, "qty_col")

    # Revenue Logic
    if r_col: df['_rev'] = robust_numeric(df, r_col)
    else: df['_rev'] = robust_numeric(df, pr_col) * robust_numeric(df, q_col)

    # Profit Logic
    if prof_col: df['_prof'] = robust_numeric(df, prof_col)
    else: df['_prof'] = df['_rev'] * 0.20

    final_p = p_col if p_col and 'id' not in p_col.lower() else cols[0]

    metrics = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2),
        "best_seller": str(df.groupby(final_p)['_rev'].sum().idxmax()),
        "top_profit_prod": str(df.groupby(final_p)['_prof'].sum().idxmax()),
        "p_col": final_p
    }
    return metrics, df

