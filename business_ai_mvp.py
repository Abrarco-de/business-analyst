import pandas as pd
import numpy as np
import google.generativeai as genai
from groq import Groq
import json
import re

def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        groq_client = Groq(api_key=groq_key)
        return groq_client
    except Exception:
        return None

def process_business_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except:
        return None

def gemini_get_schema(columns):
    """Uses Gemini to identify column roles with a strict filter against IDs."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analyze these columns: {list(columns)}
        
        Identify the correct column names for these roles. 
        CRITICAL RULE: For 'product_col', you MUST choose a descriptive column like 'Category', 'Sub Category', or 'Product'. 
        NEVER choose 'Order ID', 'Transaction ID', or any column containing 'ID', 'Date', or 'Time'.
        
        Return ONLY a valid JSON:
        {{
            "product_col": "exact name of product or category column",
            "revenue_col": "exact name of total sales/revenue column (or 'None')",
            "profit_col": "exact name of profit column (or 'None')",
            "price_col": "exact name of unit price column",
            "qty_col": "exact name of quantity column"
        }}
        """
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            schema = json.loads(json_match.group())
            # Secondary Safety Check: If AI still picked an ID, manually override
            p_low = schema['product_col'].lower()
            if 'id' in p_low or 'transaction' in p_low or 'order' in p_low:
                raise ValueError("AI picked an ID column")
            return schema
        return None
    except:
        # ULTIMATE FALLBACK: Search for keywords manually if AI fails
        cols_list = list(columns)
        cols_lower = [c.lower() for c in cols_list]
        
        # Priority list for Product Column
        p_col = cols_list[0]
        for target in ['category', 'product', 'sub category', 'item', 'description']:
            for i, name in enumerate(cols_lower):
                if target in name and 'id' not in name:
                    p_col = cols_list[i]
                    break
            else: continue
            break
            
        return {
            "product_col": p_col,
            "revenue_col": cols_list[cols_lower.index('sales')] if 'sales' in cols_lower else "None",
            "profit_col": cols_list[cols_lower.index('profit')] if 'profit' in cols_lower else "None",
            "price_col": "None",
            "qty_col": "None"
        }

def calculate_precise_metrics(df, schema):
    def to_f(c):
        if not c or c not in df.columns or c == "None": 
            return pd.Series([0.0]*len(df))
        return pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)

    # 1. Revenue
    if schema.get("revenue_col") and schema["revenue_col"] != "None":
        df['_rev'] = to_f(schema["revenue_col"])
    else:
        df['_rev'] = to_f(schema.get("price_col")) * to_f(schema.get("qty_col"))

    # 2. Profit
    if schema.get("profit_col") and schema["profit_col"] != "None":
        df['_prof'] = to_f(schema["profit_col"])
    else:
        df['_prof'] = df['_rev'] * 0.25 

    p_col = schema.get("product_col", df.columns[0])
    
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
                {"role": "system", "content": "You are a senior SME Business Consultant in Saudi Arabia."},
                {"role": "user", "content": f"Revenue: {metrics['rev']} SAR. Profit: {metrics['prof']} SAR. Top Product: {metrics['best_seller']}. Most Profitable: {metrics['top_profit_prod']}. 3 Tips."}
            ],
            temperature=0.5,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Consultant unavailable: {str(e)}"
