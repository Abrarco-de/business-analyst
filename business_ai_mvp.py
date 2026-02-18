import pandas as pd
import json
import re
from groq import Groq
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# --- 1. ENGINE CONFIGURATION ---
def configure_dual_engines(groq_key, mistral_key):
    try:
        g_client = Groq(api_key=groq_key)
        m_client = MistralClient(api_key=mistral_key)
        return g_client, m_client
    except: return None, None

# --- 2. THE CLEANER (Groq Llama 3.3) ---
def process_business_data(groq_client, df):
    # Standardize Column Names
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    cols_list = df.columns.tolist()

    # Agent 1: Use Groq to map columns via JSON
    mapping_prompt = f"""
    Identify the column names for: Revenue, Profit, and Product Name from this list: {cols_list}.
    Return ONLY a JSON object: {{"rev": "name", "prof": "name", "prod": "name"}}
    """
    
    mapping_res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": mapping_prompt}],
        response_format={"type": "json_object"}
    )
    
    mapping = json.loads(mapping_res.choices[0].message.content)
    
    # Cleaning Logic
    def to_num(col): return pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    
    df['_rev'] = to_num(mapping['rev'])
    df['_prof'] = to_num(mapping['prof']) if mapping['prof'] in df.columns else df['_rev'] * 0.20
    
    # ADVANCED SME METRICS
    total_rev = df['_rev'].sum()
    total_prof = df['_prof'].sum()
    
    metrics = {
        "rev": round(total_rev, 2),
        "prof": round(total_prof, 2),
        "margin": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
        "vat": round(total_rev * 0.15, 2), # Saudi VAT
        "top_item": str(df.groupby(mapping['prod'])['_rev'].sum().idxmax()) if total_rev > 0 else "N/A",
        "avg_order": round(df['_rev'].mean(), 2)
    }
    
    return metrics, df

# --- 3. THE STRATEGIST (Mistral Large) ---
def get_ai_response(mistral_client, metrics, df, user_query):
    try:
        # Data sample for context
        data_context = df.head(30).to_string()
        
        prompt = f"""
        You are a Senior Saudi Business Consultant.
        METRICS: Rev: {metrics['rev']} SAR, Margin: {metrics['margin']}%, Top Item: {metrics['top_item']}.
        DATA SAMPLE: {data_context}
        
        USER QUESTION: "{user_query}"
        
        TASK: Provide a sharp, data-backed business insight. Mention SAR values.
        Give 1 actionable tip specifically for the Saudi market context.
        """
        
        messages = [ChatMessage(role="user", content=prompt)]
        response = mistral_client.chat(model="mistral-large-latest", messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Consultant Error: {str(e)}"
