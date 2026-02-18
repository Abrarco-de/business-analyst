import pandas as pd
import google.generativeai as genai
from groq import Groq
import difflib

# 1. THE ENGINE SETUP (Ensure this exact name exists)
def configure_engines(gemini_key, groq_key):
    try:
        genai.configure(api_key=gemini_key)
        return Groq(api_key=groq_key)
    except Exception as e:
        print(f"Config Error: {e}")
        return None

# 2. DATA PROCESSING
def calculate_precise_metrics(df):
    df.columns = [str(c).strip().replace('ï»¿', '') for c in df.columns]
    
    # Simple mapping for robustness
    r_col = next((c for c in df.columns if 'sale' in c.lower() or 'revenue' in c.lower()), df.columns[0])
    p_col = next((c for c in df.columns if 'profit' in c.lower()), None)
    
    df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
    df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col else df['_rev'] * 0.20
    
    m = {
        "rev": round(df['_rev'].sum(), 2),
        "prof": round(df['_prof'].sum(), 2),
        "vat": round(df['_rev'].sum() * 0.15, 2),
        "margin": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0
    }
    return m, df

# 3. INTELLIGENCE BRIDGE
def get_intelligent_answer(groq_client, df, user_query, m):
    try:
        # Step A: Groq Research
        data_summary = df.head(50).to_string()
        research_prompt = f"Analyze for query: {user_query}. Data summary: {data_summary}"
        
        research = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": research_prompt}]
        )
        fact_sheet = research.choices[0].message.content

        # Step B: Gemini Consultation (Using Dynamic Name Discovery)
        available_models = [model.name for model in genai.list_models() if 'generateContent' in model.supported_generation_methods]
        # Pick best available or fallback
        target = "models/gemini-1.5-flash"
        for potential in ["models/gemini-2.0-flash", "models/gemini-3-flash"]:
            if potential in available_models:
                target = potential
                break
        
        brain = genai.GenerativeModel(target)
        consult_prompt = f"Facts: {fact_sheet}\nStats: {m}\nQuestion: {user_query}. Give a strategic tip."
        response = brain.generate_content(consult_prompt)
        return response.text
    except Exception as e:
        return f"Bridge Error: {str(e)}"
