import pandas as pd
import numpy as np
import google.generativeai as genai
from groq import Groq
import json
import re

def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except: return None

def process_business_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        # Standardize headers: No BOM, No extra spaces
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def gemini_get_schema(columns):
    """Uses Gemini to identify roles, with strict instructions to avoid IDs."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Columns: {list(columns)}
        Identify the BEST matching column for these roles. 
        RULES:
        - 'product_col': MUST be a category or item name (e.g., 'Product', 'Category'). NEVER choose an ID or Transaction number.
        - 'revenue_col': The total sales amount. If no total column exists, return 'None'.
        - 'profit_col': The profit column. If missing, return 'None'.
        Return ONLY valid JSON:
        {{
            "product_col": "string",
            "revenue_col": "string or 'None'",
            "profit_col": "string or 'None'",
            "price_col": "string or 'None'",
            "qty_col": "string or 'None'"
        }}
        """
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(json_match.group())
    except: return None

def calculate_precise_metrics(df, schema):
    """Robust math that handles missing columns and text in numbers."""
    
    def get_col_safe(key_name):
        """Finds the column name even if case is different."""
        target = schema.get(key_name, "None")
        if not target or target == "None": return None
        # Case-insensitive match
        for actual_col in df.columns:
            if actual_col.lower() == target.lower():
                return actual_col
        return None

    def to_numeric_series(col_name):
        if not col_name: return pd.Series([0.0]*len(df))
        # Remove commas, currency symbols, and spaces, then convert
        clean_s = df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True)
        return pd.to_numeric(clean_s, errors='coerce').fillna(0.0)

    # 1. Identify Product Column (Filtering IDs)
    p_col = get_col_safe("product_col")
    if not p_col or any(x in p_col.lower() for x in ['id', 'number', 'transaction']):
        # Fallback search for a better category column
        for c in df.columns:
            if any(x in c.lower() for x in ['product', 'category', 'item', 'type']) and 'id' not in c.lower():
                p_col = c
                break
        if not p_col: p_col = df.columns[0]

    # 2. Calculate Revenue
    rev_col = get_col_safe("revenue_col")
    if rev_col:
        df['_rev'] = to_numeric_series(rev_col)
    else:
        # Fallback to Price * Qty
        p_price = get_col_safe("price_col")
        p_qty = get_col_safe("qty_col")
        df['_rev'] = to_numeric_series(p_price) * to_numeric_series(p_qty)

    # 3. Calculate Profit
    prof_col = get_col_safe("profit_col")
    if prof_col:
        df['_prof'] = to_numeric_series(prof_col)
    else:
        df['_prof'] = df['_rev'] * 0.25 # 25% Margin Estimate

    metrics = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2),
        "best_seller": str(df.groupby(p_col)['_rev'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "top_profit_prod": str(df.groupby(p_col)['_prof'].sum().idxmax()) if df['_prof'].sum() > 0 else "N/A",
        "p_col": p_col
    }
    return metrics, df

def groq_get_insights(client, metrics):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a senior Saudi Business Consultant. Provide 3 high-level growth tips."},
                {"role": "user", "content": f"Data: Revenue {metrics['rev']} SAR, Profit {metrics['prof']}, Top Item {metrics['best_seller']}. Recommend strategies."}
            ],
            temperature=0.5,
        )
        return completion.choices[0].message.content
    except: return "Consultant currently analyzing data..."
