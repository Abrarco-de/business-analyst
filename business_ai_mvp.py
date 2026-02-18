import pandas as pd
import numpy as np
import google.generativeai as genai
import json, re, difflib

# 1. THE SCHEMA BIBLE (Add any common names you see in your datasets here)
SCHEMA_MAP = {
    "product_col": ["Product", "Item", "Category", "Sub Category", "Product Name", "Description", "Brand"],
    "revenue_col": ["Sales", "Total Amount", "Total", "Revenue", "Amount", "Subtotal", "Price per Unit"], 
    "profit_col": ["Profit", "Margin", "Earnings", "Net Profit", "Gain"],
    "qty_col": ["Quantity", "Qty", "Count", "Units Sold", "Vol"]
}

def clean_column_names(df):
    """Standardize headers: remove spaces, dots, and hidden characters."""
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    return df

def find_best_column(actual_cols, target_key):
    """Logic: 1. Direct Check -> 2. Fuzzy Match -> 3. None"""
    possible_names = SCHEMA_MAP.get(target_key, [])
    
    # Step 1: Exact/Lowercase Match
    for name in possible_names:
        for col in actual_cols:
            if col.lower() == name.lower():
                return col
                
    # Step 2: Fuzzy Logic (difflib)
    for name in possible_names:
        matches = difflib.get_close_matches(name.lower(), [c.lower() for c in actual_cols], n=1, cutoff=0.8)
        if matches:
            # Return the original case version of the match
            return next(c for c in actual_cols if c.lower() == matches[0])
            
    return None

def ai_fallback_mapping(columns):
    """The last resort: Ask the AI to guess based on business knowledge."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Columns: {list(columns)}. Return JSON with keys 'product_col', 'revenue_col', 'profit_col' matching these headers. NO IDs."
        response = model.generate_content(prompt)
        return json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group())
    except: return {}

def robust_numeric_conversion(series):
    """Turns '$1,200.50 SAR' into 1200.50."""
    if series is None: return pd.Series([0.0])
    # Remove everything except numbers, dots, and minus signs
    clean = series.astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0.0)

def process_and_calculate(df):
    df = clean_column_names(df)
    cols = df.columns
    
    # Logic Phase
    p_col = find_best_column(cols, "product_col")
    r_col = find_best_column(cols, "revenue_col")
    prof_col = find_best_column(cols, "profit_col")
    
    # AI Fallback Phase (if major columns are missing)
    if not p_col or not r_col:
        ai_guess = ai_fallback_mapping(cols)
        p_col = p_col or ai_guess.get("product_col")
        r_col = r_col or ai_guess.get("revenue_col")
        prof_col = prof_col or ai_guess.get("profit_col")

    # Math Phase
    df['_rev'] = robust_numeric_conversion(df[r_col] if r_col else None)
    df['_prof'] = robust_numeric_conversion(df[prof_col] if prof_col else None)
    
    # If profit is missing, estimate it as 20% of revenue
    if not prof_col or df['_prof'].sum() == 0:
        df['_prof'] = df['_rev'] * 0.20

    return {
        "revenue": df['_rev'].sum(),
        "profit": df['_prof'].sum(),
        "best_item": df.groupby(p_col)['_rev'].sum().idxmax() if p_col else "Unknown",
        "p_col": p_col
    }
