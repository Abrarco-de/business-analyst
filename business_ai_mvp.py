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
    "product_col": ["Product", "Category", "Item", "Sub Category", "Description", "Product Name", "Product Category"],
    "revenue_col": ["Sales", "Total Amount", "Revenue", "Amount", "Subtotal", "Total Sales"],
    "profit_col": ["Profit", "Margin", "Earnings", "Net Profit", "Gain"],
    "price_col": ["Price", "Unit Price", "Rate", "Price per Unit"],
    "qty_col": ["Quantity", "Qty", "Count", "Units Sold"]
}

def clean_column_names(df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    return df

def find_best_column(actual_cols, target_key):
    possible_names = SCHEMA_MAP.get(target_key, [])
    # Direct Match
    for name in possible_names:
        for col in actual_cols:
            if col.lower() == name.lower(): return col
    # Fuzzy Match
    for name in possible_names:
        matches = difflib.get_close_matches(name.lower(), [c.lower() for c in actual_cols], n=1, cutoff=0.8)
        if matches:
            return next(c for c in actual_cols if c.lower() == matches[0])
    return None

def robust_numeric(df, col_name):
    if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
    clean = df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0.0)

# --- 3. METRIC CALCULATION (The Foundation) ---
def calculate_precise_metrics(df):
    df = clean_column_names(df)
    cols = df.columns
    
    # Identify Columns
    p_col = find_best_column(cols, "product_col")
    r_col = find_best_column(cols, "revenue_col")
    prof_col = find_best_column(cols, "profit_col")
    pr_col = find_best_column(cols, "price_col")
    q_col = find_best_column(cols, "qty_col")

    # Revenue Logic
    if r_col:
        df['_rev'] = robust_numeric(df, r_col)
    else:
        df['_rev'] = robust_numeric(df, pr_col) * robust_numeric(df, q_col)

    # Profit Logic
    if prof_col:
        df['_prof'] = robust_numeric(df, prof_col)
    else:
        df['_prof'] = df['_rev'] * 0.20 # 20% fallback margin

    # Ensure a valid product column (reject IDs)
    final_p = p_col if p_col and 'id' not in p_col.lower() else cols[0]

    metrics = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2),
        "best_seller": str(df.groupby(final_p)['_rev'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "top_profit_prod": str(df.groupby(final_p)['_prof'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "p_col": final_p,
        "avg_margin": round((df['_prof'].sum() / df['_rev'].sum()) * 100, 2) if df['_rev'].sum() > 0 else 0
    }
    return metrics, df

# --- 4. THE INTELLIGENCE BRIDGE (Gemini Researcher + Groq Analyst) ---
def get_intelligent_answer(groq_client, df, user_query, metrics):
    try:
        # Agent 1: Gemini (Data Researcher)
        # Using 'models/gemini-1.5-flash-latest' to avoid 404 errors
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Summary for context
        summary_context = f"""
        Business Summary:
        - Total Revenue: {metrics['rev']} SAR
        - Total Profit: {metrics['prof']} SAR
        - Net Margin: {metrics['avg_margin']}%
        - Top Product: {metrics['best_seller']}
        - Most Profitable Product: {metrics['top_profit_prod']}
        """

        research_prompt = f"""
        You are a Data Researcher analyzing a Saudi business dataset.
        Question: "{user_query}"
        
        Current Metrics: {summary_context}
        Available Columns: {list(df.columns)}
        
        Task: 
        Scan the raw data (snapshot below) to find specific facts related to the question.
        Focus on trends, specific product names, or geographical data if available.
        
        Data Snapshot:
        {df.head(50).to_string()}
        
        Return a concise "Fact Sheet" for the Strategic Analyst.
        """
        
        research_response = model.generate_content(research_prompt)
        fact_sheet = research_response.text

        # Agent 2: Groq (Strategic Consultant)
        analysis_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Senior Strategic Business Analyst. Use the Fact Sheet to give a data-backed response. Mention SAR values and provide 1-2 actionable tips based on the numbers."},
                {"role": "user", "content": f"Fact Sheet: {fact_sheet}\n\nUser Question: {user_query}"}
            ],
            temperature=0.3
        )
        
        return analysis_completion.choices[0].message.content
    except Exception as e:
        return f"Intelligence Bridge Error: {str(e)}"

# --- 5. INITIAL INSIGHT GENERATOR ---
def get_intelligent_answer(groq_client, df, user_query, metrics):
    try:
        # Try the most stable model name
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
        except:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        summary_context = f"""
        Stats: Revenue {metrics['rev']} SAR, Profit {metrics['prof']} SAR, Top Item: {metrics['best_seller']}
        """

        # We take a larger chunk of data but keep it clean
        data_snapshot = df.head(100).to_string()
        
        research_prompt = f"""
        User Question: "{user_query}"
        {summary_context}
        
        Dataset Columns: {list(df.columns)}
        Data Snapshot:
        {data_snapshot}
        
        Extract ONLY the specific facts and numbers from the data that answer the question.
        """
        
        response = model.generate_content(research_prompt)
        fact_sheet = response.text

        # Groq handles the strategy
        analysis = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Business Analyst. Use the Fact Sheet provided to answer the user query accurately."},
                {"role": "user", "content": f"Fact Sheet: {fact_sheet}\n\nQuestion: {user_query}"}
            ],
            temperature=0.2
        )
        return analysis.choices[0].message.content
    except Exception as e:
        # This will tell us if it's still a 404 or something else
        return f"AI Bridge Error: {str(e)}"


