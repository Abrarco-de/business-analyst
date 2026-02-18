import pandas as pd
import numpy as np
import google.generativeai as genai
import json

def configure_ai(api_key):
    if not api_key: return False
    try:
        genai.configure(api_key=api_key, transport='rest')
        return True
    except: return False

def process_business_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding='latin1') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def gemini_schema_mapper(columns):
    """Gemini decides the schema once at the start."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analyze these spreadsheet columns: {list(columns)}
        Identify which column matches these business needs. Return ONLY a JSON object:
        {{
            "product_col": "exact column name for product/category",
            "revenue_col": "exact column name for total sales/amount",
            "profit_col": "exact column name for profit (or 'None')",
            "price_col": "exact column name for unit price (if no total sales col)",
            "qty_col": "exact column name for quantity"
        }}
        """
        response = model.generate_content(prompt)
        # Clean the response text to ensure it's valid JSON
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        # Fallback if Gemini is busy
        return {"product_col": columns[0], "revenue_col": columns[-1], "profit_col": "None"}

def generate_logic_insights(df, schema):
    """Pure Python Logic - No AI Busy errors here."""
    def to_num(c):
        if not c or c not in df.columns or c == "None": return pd.Series([0.0]*len(df))
        return pd.to_numeric(df[c].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0.0)

    # 1. Revenue & Profit Math
    if schema.get("revenue_col") and schema["revenue_col"] in df.columns:
        df['_rev'] = to_num(schema["revenue_col"])
    else:
        df['_rev'] = to_num(schema.get("price_col")) * to_num(schema.get("qty_col"))

    if schema.get("profit_col") and schema["profit_col"] != "None":
        df['_prof'] = to_num(schema["profit_col"])
    else:
        df['_prof'] = df['_rev'] * 0.25 # Default 25% margin

    # 2. Key Metrics
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    p_col = schema["product_col"]
    
    best_seller = df.groupby(p_col)['_rev'].sum().idxmax() if total_rev > 0 else "N/A"
    most_profitable = df.groupby(p_col)['_prof'].sum().idxmax() if total_prof > 0 else "N/A"

    # 3. Code-Generated Text Insights
    top_share = (df.groupby(p_col)['_rev'].sum().max() / total_rev * 100) if total_rev > 0 else 0
    
    insights = [
        f"✅ **Revenue Leader:** {best_seller} accounts for {top_share:.1f}% of total revenue.",
        f"✅ **ZATCA (15% VAT):** Estimated tax liability is {total_rev * 0.15:,.2f} SAR.",
        f"✅ **Profitability:** Your business is currently operating at a { (total_prof/total_rev*100) if total_rev > 0 else 0:.1f}% net margin."
    ]

    return {
        "revenue": total_rev,
        "profit": total_prof,
        "vat": total_rev * 0.15,
        "best_seller": best_seller,
        "most_profitable": most_profitable,
        "insights": insights,
        "df": df,
        "p_col": p_col
    }
