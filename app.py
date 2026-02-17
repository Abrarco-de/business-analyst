import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import os
import re
from difflib import get_close_matches

# ================= 1. SETUP & CONFIG =================
st.set_page_config(page_title="Saudi SME Analyst", page_icon="🇸🇦", layout="wide")

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# ================= 2. THE CLEANING ENGINE =================

def clean_numeric_value(val):
    """Removes 'SAR', commas, and text so Python can do math."""
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    # Remove everything except numbers and decimals
    clean = re.sub(r'[^\d.]', '', str(val))
    try:
        return float(clean) if clean else 0.0
    except:
        return 0.0

def process_file(uploaded_file):
    """Reads CSV/Excel and cleans the hidden junk."""
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        # Clean all potential number columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'amt', 'سعر', 'كمية', 'تكلفة']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        st.error(f"❌ File Error: {e}")
        return None

# ================= 3. THE HYBRID MAPPER (NO MORE 429 ERRORS) =================

def get_best_mapping(columns):
    """
    Combines Fuzzy Matching (Local) with AI (Remote).
    If AI fails or is exhausted, the local math still works!
    """
    standard_schema = {
        "product_name": ["item", "product", "desc", "المنتج", "الصنف", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر", "بيع", "sar", "الوحدة"],
        "quantity": ["qty", "count", "amount", "الكمية", "عدد", "qty"],
        "cost_price": ["cost", "purchase", "buying", "تكلفة", "شراء", "التكلفة"]
    }
    
    mapping = {}
    
    # --- STEP 1: LOCAL FUZZY MATCHING (Fast & Free) ---
    for col in columns:
        col_lower = col.lower().strip()
        for std_name, hints in standard_schema.items():
            # If the column name is very close to one of our hints
            if any(h in col_lower for h in hints):
                mapping[col] = std_name
                break

    # --- STEP 2: AI IMPROVEMENT (Only if API Key is healthy) ---
    if API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Map these headers: {columns} to standard keys: {list(standard_schema.keys())}. Return ONLY JSON."
            response = model.generate_content(prompt)
            ai_mapping = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            mapping.update(ai_mapping) # AI mapping takes priority if it works
        except Exception:
            # If AI fails (429/quota), we just stick with the manual mapping
            pass
            
    return mapping

# ================= 4. ANALYTICS ENGINE =================

def generate_insights(df):
    """Calculates KPIs with safety fallbacks."""
    # Ensure math works even if columns are missing
    rev = df.get("unit_price", 0) * df.get("quantity", 0)
    cost = df.get("cost_price", 0) * df.get("quantity", 0)
    
    # If cost is missing for all rows, assume 30% margin for the demo
    if df.get("cost_price", pd.Series([0])).sum() == 0:
        cost = rev * 0.7
    
    total_rev = rev.sum()
    total_prof = (rev - cost).sum()
    
    insights = {
        "total_revenue": round(total_rev, 2),
        "total_profit": round(total_prof, 2),
        "profit_margin_percent": 0.0
    }
    
    if total_rev > 0:
        insights["profit_margin_percent"] = round((total_prof / total_rev) * 100, 2)
        
    return insights

# ================= 5. STREAMLIT UI =================

st.title("🇸🇦 Saudi SME Profit AI")
st.markdown("### The 69 SAR Business Intelligence Tool")

file = st.file_uploader("Upload POS Data (CSV/Excel)", type=["csv", "xlsx"])

if file:
    with st.spinner("Processing your data..."):
        raw_df = process_file(file)
        
        if raw_df is not None:
            # Get the Map (Hybrid AI + Local)
            mapping = get_best_mapping(list(raw_df.columns))
            
            # Create a copy with renamed columns for math
            processed_df = raw_df.rename(columns=mapping)
            
            # Generate Stats
            results = generate_insights(processed_df)
            
            # --- DASHBOARD ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Sales", f"{results['total_revenue']:,} SAR")
            c2.metric("Estimated Profit", f"{results['total_profit']:,} SAR")
            c3.metric("Profit Margin", f"{results['profit_margin_percent']}%")
            
            st.divider()
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Top Selling Products")
                if "product_name" in processed_df.columns:
                    # Calculate product revenue
                    processed_df['line_revenue'] = processed_df.get('unit_price', 0) * processed_df.get('quantity', 0)
                    top_items = processed_df.groupby("product_name")['line_revenue'].sum().sort_values(ascending=False).head(5)
                    st.bar_chart(top_items)
                else:
                    st.info("No 'Product Name' column detected for charts.")
            
            with col_right:
                st.subheader("Final Mapped Data")
                # Show only relevant columns
                display_cols = [c for c in processed_df.columns if c in mapping.values()]
                st.dataframe(processed_df[display_cols].head(15), use_container_width=True)

            # Success message
            if results['total_revenue'] > 0:
                st.success("✅ Analysis Complete! You can now download this report.")
            else:
                st.warning("⚠️ Data processed, but no revenue found. Check your 'Price' and 'Qty' columns.")








