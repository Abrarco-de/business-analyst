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

def groq_get_insights(client, metrics):
    try:
        # Create a detailed data string for the AI to "chew" on
        data_summary = f"""
        - Total Revenue: {metrics['rev']} SAR
        - Total Profit: {metrics['prof']} SAR
        - Net Margin: {round((metrics['prof']/metrics['rev'])*100, 2) if metrics['rev'] > 0 else 0}%
        - Top Product by Revenue: {metrics['best_seller']}
        - Top Product by Profit: {metrics['top_profit_prod']}
        - Estimated VAT Liability: {metrics['vat']} SAR
        """

        # Detailed instructions to avoid generic advice
        system_prompt = """
        You are a Senior Strategic Business Analyst specializing in the Saudi retail market. 
        Your task is to analyze the provided metrics and give 3 UNIQUE, data-specific insights.
        
        RULES:
        1. NO generic advice like 'improve marketing' or 'save costs'.
        2. If 'Best Seller' is different from 'Top Profit Maker', analyze why (Volume vs Margin).
        3. Mention the specific product names and numbers provided.
        4. Focus on the 'Margin Gap' or 'VAT Impact' if relevant.
        5. Use a professional, executive tone.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the business performance data: {data_summary}. Provide a surgical growth strategy."}
            ],
            temperature=0.3, # Lower temperature = more factual/logical
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Analyst is busy: {str(e)}"
