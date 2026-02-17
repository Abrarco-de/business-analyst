import pandas as pd
import json
import os
import google.generativeai as genai
import streamlit as st

# ================= CONFIG =================
# Tip: In 2026, Google recommends using 'gemini-2.5-flash' for high-volume SME tasks
MODEL_ID = 'gemini-2.5-flash' 

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("🔑 API Key is missing. Add it to your environment variables or Streamlit secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ================= AI HEADER MAPPING =================

def get_header_mapping(dirty_columns):
    prompt = f"""
    You are a data cleaning agent for a Saudi Arabian business. 
    Map these messy headers: {dirty_columns} 
    to this schema: [transaction_id, timestamp, product_name, quantity, unit_price, cost_price].
    
    Return ONLY a JSON object. Example: {{"Item": "product_name", "Price": "unit_price"}}
    """
    
    # Initialize the NEW model
    try:
        model = genai.GenerativeModel(MODEL_ID)
        response = model.generate_content(prompt)
        
        # Clean text from Markdown backticks
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"🤖 AI Error: {e}")
        return {}

# ================= FILE PROCESSING =================

def process_business_file(uploaded_file):
    try:
        # Step 1: Read the file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Step 2: Use AI to find the right columns
        mapping = get_header_mapping(list(df.columns))
        
        if not mapping:
            st.warning("Could not map columns automatically.")
            return df

        # Step 3: Transform data
        df = df.rename(columns=mapping)
        
        # Only keep the columns we actually found
        existing_mapped_cols = [v for v in mapping.values() if v in df.columns]
        df = df[existing_mapped_cols]

        # Step 4: Numeric Cleanup (Crucial for SAR calculations)
        for col in ["quantity", "unit_price", "cost_price"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        return df
    except Exception as e:
        st.error(f"❌ File Processing Error: {e}")
        return None

# ================= STREAMLIT UI =================
st.title("🇸🇦 Business Analyst AI")
file = st.file_uploader("Upload POS Data", type=["csv", "xlsx"])

if file:
    processed_df = process_business_file(file)
    if processed_df is not None:
        st.write("### Cleaned Data Preview", processed_df.head())
        
        # Basic Stats for the 69 SAR value prop
        revenue = (processed_df['unit_price'] * processed_df['quantity']).sum()
        st.metric("Total Revenue", f"{revenue:,.2f} SAR")







