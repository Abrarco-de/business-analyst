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
    # Initialize defaults to prevent KeyError in UI
    metrics = {
        "rev": 0, "prof": 0, "margin": 0, "vat": 0,
        "best_product": "No data analyzed yet"
    }
    
    try:
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Smart Column Mapping
        r_col = next((c for c in df.columns if any(x in c.lower() for x in ['rev', 'sale', 'amount'])), df.columns[0])
        p_col = next((c for c in df.columns if any(x in c.lower() for x in ['prof', 'net'])), None)
        prod_col = next((c for c in df.columns if any(x in c.lower() for x in ['prod', 'item', 'desc'])), df.columns[0])

        # 2. Clean Numeric Data
        df['_rev'] = pd.to_numeric(df[r_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
        df['_prof'] = pd.to_numeric(df[p_col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0) if p_col else df['_rev'] * 0.20
        
        # 3. Calculate Advanced Metrics
        total_rev = df['_rev'].sum()
        total_prof = df['_prof'].sum()
        
        # Find Top 3 Products for "Data Exchange"
        top_df = df.groupby(prod_col)['_prof'].sum().sort_values(ascending=False).head(3)
        top_list = ", ".join([f"{n} ({v:,.0f} SAR)" for n, v in top_df.items()])

        metrics.update({
            "rev": round(total_rev, 2),
            "prof": round(total_prof, 2),
            "margin": round((total_prof / total_rev * 100), 2) if total_rev > 0 else 0,
            "best_product": top_list,
            "vat": round(total_rev * 0.15, 2)
        })
    except Exception as e:
        print(f"Cleaning Error: {e}")
        
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
