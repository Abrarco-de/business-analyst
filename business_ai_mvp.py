import pandas as pd
import numpy as np
import google.generativeai as genai
from groq import Groq
import json, re, difflib

# --- 1. ENGINE CONFIGURATION ---
def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except Exception:
        return None

# --- 2. THE SCHEMA BIBLE (Rule-Based Mapping) ---
SCHEMA_MAP = {
    "product_col": ["Product", "Category", "Sub Category", "Item", "Description", "Product Category", "Product Name"],
    "revenue_col": ["Sales", "Total Amount", "Total", "Revenue", "Amount", "Subtotal", "Total Sales"],
    "profit_col": ["Profit", "Margin", "Earnings", "Net Profit", "Gain"],
    "price_col": ["Price", "Unit Price", "Price per Unit", "Rate"],
    "qty_col": ["Quantity", "Qty", "Count", "Units Sold"]
}

def clean_column_names(df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    return df

def find_best_column(actual_cols, target_key):
    """Uses direct match and fuzzy logic before calling AI."""
    possible_names = SCHEMA_MAP.get(target_key, [])
    # Direct Match
    for name in possible_names:
        for col in actual_cols:
            if col.lower() == name.lower(): return col
    # Fuzzy Match (80% similarity)
    for name in possible_names:
        matches = difflib.get_close_matches(name.lower(), [c.lower() for c in actual_cols], n=1, cutoff=0.8)
        if matches:
            return next(c for c in actual_cols if c.lower() == matches[0])
    return None

# --- 3. AI FALLBACK ---
def ai_fallback_mapping(columns):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these headers to business roles: {list(columns)}. Return ONLY JSON: {{'product_col': '', 'revenue_col': '', 'profit_col': '', 'price_col': '', 'qty_col': ''}}. No IDs."
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(json_match.group()) if json_match else {}
    except: return {}

# --- 4. ADVANCED MATH & METRICS ---
def robust_numeric(df, col_name):
    if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
    # Regex to keep digits, dots, and negative signs only (removes SAR, commas, etc)
    clean = df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0.0)

def calculate_precise_metrics(df):
    df = clean_column_names(df)
    cols = df.columns
    
    # Mapping
    p_col = find_best_column(cols, "product_col")
    r_col = find_best_column(cols, "revenue_col")
    prof_col = find_best_column(cols, "profit_col")
    pr_col = find_best_column(cols, "price_col")
    q_col = find_best_column(cols, "qty_col")

    # If key columns missing, ask Gemini
    if not p_col or (not r_col and not pr_col):
        ai_map = ai_fallback_mapping(cols)
        p_col = p_col or ai_map.get("product_col")
        r_col = r_col or ai_map.get("revenue_col")
        prof_col = prof_col or ai_map.get("profit_col")
        pr_col = pr_col or ai_map.get("price_col")
        q_col = q_col or ai_map.get("qty_col")

    # Final logic for Revenue
    if r_col and r_col != "None":
        df['_rev'] = robust_numeric(df, r_col)
    else:
        df['_rev'] = robust_numeric(df, pr_col) * robust_numeric(df, q_col)

    # Final logic for Profit
    if prof_col and prof_col != "None":
        df['_prof'] = robust_numeric(df, prof_col)
    else:
        df['_prof'] = df['_rev'] * 0.20 # 20% fallback margin

    # Identify valid product column (avoid IDs)
    final_p = p_col if p_col and 'id' not in p_col.lower() else cols[0]

    metrics = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2),
        "best_seller": str(df.groupby(final_p)['_rev'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "top_profit_prod": str(df.groupby(final_p)['_prof'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "p_col": final_p
    }
    return metrics, df

def get_intelligent_answer(groq_client, df, user_query, metrics):
    """Bridge Gemini's data extraction with Groq's strategic reasoning."""
    try:
        # Step 1: Gemini extracts specific data points from the full DF
        # We give Gemini a sample of the data to understand the structure
        sample_data = df.head(10).to_string()
        
        researcher_model = genai.GenerativeModel('gemini-1.5-flash')
        research_prompt = f"""
        You are a Data Researcher. Look at this user question: "{user_query}"
        Based on the dataset columns {list(df.columns)}, find the specific facts.
        
        If the user asks about a specific month, product, or trend, summarize the specific numbers from the data.
        Dataset Summary: Total Rows {len(df)}, Top Item: {metrics['best_seller']}.
        
        Return a concise FACT SHEET for the Analyst.
        """
        
        research_response = researcher_model.generate_content(research_prompt)
        fact_sheet = research_response.text

        # Step 2: Groq analyzes Gemini's findings
        analysis_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Strategic Business Analyst. Use the provided Fact Sheet to answer the user query. Be specific, use numbers, and avoid generic advice."},
                {"role": "user", "content": f"Fact Sheet from Researcher: {fact_sheet}\n\nUser Question: {user_query}"}
            ],
            temperature=0.2
        )
        
        return analysis_completion.choices[0].message.content
    except Exception as e:
        return f"Intelligence Bridge Error: {str(e)}"
