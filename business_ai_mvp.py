import pandas as pd
from groq import Groq
from mistralai import Mistral

def configure_dual_engines(groq_key, mistral_key):
    try:
        g = Groq(api_key=groq_key)
        m = Mistral(api_key=mistral_key)
        return g, m
    except: return None, None

def process_business_data(groq_client, df):
    metrics = {"rev": 0, "prof": 0, "margin": 0, "vat": 0, "best_product": "No data found"}
    
    try:
        # Standardize columns
        df.columns = [str(c).strip() for c in df.columns]

        # --- IMPROVED PRODUCT DETECTION ---
        # 1. Look for columns containing "Name" or "Description" first
        prod_keywords = ['name', 'desc', 'item', 'product', 'title']
        avoid_keywords = ['id', 'code', 'sku', 'serial', 'no', 'number']
        
        # Priority 1: Has "name/desc" but NOT "id/code"
        prod_col = next((c for c in df.columns if any(k in c.lower() for k in prod_keywords) 
                         and not any(a in c.lower() for a in avoid_keywords)), None)
        
        # Priority 2: Just has "name/desc/item"
        if not prod_col:
            prod_col = next((c for c in df.columns if any(k in c.lower() for k in prod_keywords)), df.columns[0])

        # Standard mapping for Revenue and Profit
        r_col = next((c for c in df.columns if any(x in c.lower() for x in ['rev', 'sale', 'amount'])), df.columns[0])
        p_col = next((c for c in df.columns if any(x in c.lower() for x in ['prof', 'net'])), None)

        # Numeric Conversion
        df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
        df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col else df['_rev'] * 0.20
        
        # Calculate Top 3
        top_df = df.groupby(prod_col)['_prof'].sum().sort_values(ascending=False).head(3)
        top_list = ", ".join([f"{n} ({v:,.0f} SAR)" for n, v in top_df.items()])

        metrics.update({
            "rev": round(df['_rev'].sum(), 2),
            "prof": round(df['_prof'].sum(), 2),
            "margin": round((df['_prof'].sum() / df['_rev'].sum() * 100), 2) if df['_rev'].sum() > 0 else 0,
            "best_product": top_list
        })
    except Exception as e:
        st.error(f"Detection Error: {e}")
        
    return metrics, df

# FIXED: Now takes EXACTLY 4 arguments to match the call in app.py
def get_ai_response(mistral_client, metrics, df, user_query):
    try:
        # Pass the calculated metrics into the Mistral Prompt
        prompt = f"""
        CONTEXT: Saudi SME Business Analysis.
        METRICS: Revenue {metrics['rev']} SAR, Profit {metrics['prof']} SAR, Margin {metrics['margin']}%.
        TOP PRODUCTS: {metrics['best_product']}
        
        USER QUESTION: {user_query}
        
        STRICT INSTRUCTIONS: 
        1. Be very brief (max 2 sentences).
        2. Use the 'TOP PRODUCTS' data above to answer specifically.
        3. If it's a greeting, just say 'Welcome!'
        """
        
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

