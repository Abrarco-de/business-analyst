import pandas as pd
import google.generativeai as genai
import json
import re

# ================= 1. AI CONFIG =================

def configure_ai(api_key):
    """Initializes the Gemini connection."""
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

# ================= 2. DATA CLEANING =================

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

def process_business_file(uploaded_file):
    """Reads CSV/Excel and cleans the hidden junk."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        # Standardize numeric columns immediately
        for col in df.columns:
            if any(k in col.lower() for k in ['price', 'cost', 'qty', 'total', 'سعر', 'كمية', 'تكلفة']):
                df[col] = df[col].apply(clean_numeric_value)
        return df
    except Exception as e:
        print(f"File Processing Error: {e}")
        return None

# ================= 3. HEADER MAPPING =================

def get_header_mapping(columns, model_name='gemini-1.5-flash'):
    """
    Maps messy POS headers to our standard schema.
    Falls back to manual mapping if the API fails (429 error).
    """
    # 1. Manual Fallback Rules (Arabic & English)
    fallback_map = {}
    schema_hints = {
        "product_name": ["item", "product", "desc", "المنتج", "الصنف", "اسم"],
        "unit_price": ["price", "rate", "sale", "سعر", "بيع", "sar", "الوحدة"],
        "quantity": ["qty", "count", "amount", "الكمية", "عدد"],
        "cost_price": ["cost", "purchase", "buying", "تكلفة", "شراء", "التكلفة"]
    }

    # 2. Try AI First
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"Map these headers: {columns} to standard keys: {list(schema_hints.keys())}. Return ONLY JSON."
        response = model.generate_content(prompt)
        ai_map = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
        return ai_map
    except Exception:
        # 3. Use Fuzzy Fallback if AI is exhausted
        for col in columns:
            col_lower = col.lower().strip()
            for std_name, hints in schema_hints.items():
                if any(h in col_lower for h in hints):
                    fallback_map[col] = std_name
                    break
        return fallback_map

# ================= 4. INSIGHTS ENGINE =================

def generate_insights(df):
    """Calculates Revenue, Profit, and Margin."""
    # Ensure math works even if columns are missing via .get()
    rev = df.get("unit_price", 0) * df.get("quantity", 0)
    cost = df.get("cost_price", 0) * df.get("quantity", 0)
    
    # If cost is missing (common in Saudi SMEs), assume 30% margin for demo
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

