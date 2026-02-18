import pandas as pd
import google.generativeai as genai
from groq import Groq
import difflib

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
    return actual_cols[0] if actual_cols else None

def robust_numeric(df, col_name):
    if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
    clean = df[col_name].astype(str).str.replace(r'[^\d.-]', '', regex=True)
    return pd.to_numeric(clean, errors='coerce').fillna(0.0)

# --- 3. METRIC CALCULATION ---
def calculate_precise_metrics(df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    p_col = find_best_column(df.columns, "product_col")
    r_col = find_best_column(df.columns, "revenue_col")
    prof_col = find_best_column(df.columns, "profit_col")
    
    df['_rev'] = robust_numeric(df, r_col)
    df['_prof'] = robust_numeric(df, prof_col) if prof_col else df['_rev'] * 0.20
    
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    
    metrics = {
        "rev": round(total_rev, 2),
        "prof": round(total_prof, 2),
        "vat": round(total_rev * 0.15, 2),
        "margin": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "best_seller": str(df.groupby(p_col)['_rev'].sum().idxmax()) if total_rev > 0 else "N/A",
        "p_col": p_col
    }
    return metrics, df

# --- 4. THE ROLE-SWAP BRIDGE ---
def get_intelligent_answer(groq_client, df, user_query, metrics):
    try:
        # Step 1: Groq (Llama 3) researches the raw data
        data_sample = df.head(100).to_string()
        research_prompt = f"User asks: {user_query}. Data: {data_sample}. Extract only relevant numbers/facts."
        
        research_res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}]
        )
        fact_sheet = research_res.choices[0].message.content

        # Step 2: Gemini (The Brain) gives the business advice
        model = genai.GenerativeModel('gemini-3-flash')
        gemini_prompt = f"""
        Fact Sheet: {fact_sheet}
        SME Metrics: Revenue {metrics['rev']}, Margin {metrics['margin']}%
        User Question: {user_query}
        Provide a strategic business response for a Saudi-based SME.
        """
        response = model.generate_content(gemini_prompt)
        return response.text
    except Exception as e:
        return f"Intelligence Bridge Error: {str(e)}"

