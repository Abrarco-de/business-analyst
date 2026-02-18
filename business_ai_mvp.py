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
        # Handling CSV and Excel with Latin-1 encoding for broader compatibility
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        # Clean BOM and whitespace from headers
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except:
        return None

def gemini_get_schema(columns):
    """Uses Gemini to identify which columns play which business roles."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analyze these columns: {list(columns)}
        Identify the column names for these specific roles. Return ONLY a valid JSON:
        {{
            "product_col": "name of product or category column",
            "revenue_col": "name of total sales/revenue column (or 'None')",
            "profit_col": "name of profit column (or 'None')",
            "price_col": "name of unit price column",
            "qty_col": "name of quantity column"
        }}
        """
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(json_match.group()) if json_match else None
    except:
        return None

def calculate_precise_metrics(df, schema):
    """Deterministic math in Python - never wrong."""
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
        df['_prof'] = df['_rev'] * 0.25 # Default 25% margin estimate

    p_col = schema.get("product_col", df.columns[0])
    
    metrics = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2), # ZATCA 15%
        "best_seller": str(df.groupby(p_col)['_rev'].sum().idxmax()) if df['_rev'].sum() > 0 else "N/A",
        "top_profit_prod": str(df.groupby(p_col)['_prof'].sum().idxmax()) if df['_prof'].sum() > 0 else "N/A",
        "p_col": p_col
    }
    return metrics, df

def groq_get_insights(client, metrics):
    """Uses Groq (Llama 3) for the final business narrative."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a senior SME Business Consultant in Saudi Arabia. Provide strategic, professional advice based on provided data."},
                {"role": "user", "content": f"Total Revenue: {metrics['rev']} SAR. Net Profit: {metrics['prof']} SAR. Top Product: {metrics['best_seller']}. Most Profitable Item: {metrics['top_profit_prod']}. Give 3 specific growth insights."}
            ],
            temperature=0.5,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Consultant is currently unavailable: {str(e)}"
