import pandas as pd
import numpy as np
import google.generativeai as genai
from openai import OpenAI
import json
import re

# --- CONFIGURATION ---
def configure_engines(gemini_key, openai_key):
    try:
        genai.configure(api_key=gemini_key)
        client = OpenAI(api_key=openai_key)
        return client
    except:
        return None

def process_business_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

# --- ENGINE 1: GEMINI (The Architect) ---
def gemini_get_schema(columns):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Map these columns to business roles: {list(columns)}. Return ONLY JSON: {{'product_col': '', 'revenue_col': '', 'profit_col': '', 'price_col': '', 'qty_col': ''}}"
        response = model.generate_content(prompt)
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return {"product_col": columns[0], "revenue_col": "None"}

# --- ENGINE 2: PYTHON (The Accountant) ---
def calculate_precise_metrics(df, schema):
    def to_f(c):
        if not c or c not in df.columns or c == "None": return pd.Series([0.0]*len(df))
        return pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)

    # Revenue Logic
    if schema.get("revenue_col") != "None":
        df['_rev'] = to_f(schema["revenue_col"])
    else:
        df['_rev'] = to_f(schema.get("price_col")) * to_f(schema.get("qty_col"))

    # Profit Logic
    if schema.get("profit_col") != "None":
        df['_prof'] = to_f(schema["profit_col"])
    else:
        df['_prof'] = df['_rev'] * 0.25 # Default 25%

    m = {
        "rev": df['_rev'].sum(),
        "prof": df['_prof'].sum(),
        "vat": df['_rev'].sum() * 0.15,
        "best_seller": df.groupby(schema["product_col"])['_rev'].sum().idxmax(),
        "most_profitable": df.groupby(schema["product_col"])['_prof'].sum().idxmax(),
        "p_col": schema["product_col"]
    }
    return m, df

# --- ENGINE 3: OPENAI (The Strategist) ---
def gpt_get_strategy(client, metrics):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a CEO-level Business Consultant."},
                {"role": "user", "content": f"Data: Revenue {metrics['rev']} SAR, Profit {metrics['prof']}, Top Item {metrics['best_seller']}, Top Profit Maker {metrics['most_profitable']}. Give 3 high-level growth strategies."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"GPT Strategy currently unavailable: {str(e)}"
