import pandas as pd
import numpy as np
import google.generativeai as genai
import re

def configure_ai(api_key):
    if not api_key: return False
    try:
        genai.configure(api_key=api_key, transport='rest')
        return True
    except: return False

def process_business_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin1')
        else:
            df = pd.read_excel(uploaded_file)
        # Standardize headers: Remove BOM, strip spaces, replace mid-spaces with underscores
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def get_header_mapping(columns):
    """Refined mapping specifically for your 3 files."""
    schema_hints = {
        "product_name": ["product", "category", "sub_category", "item", "المنتج"],
        "total_amount": ["total_amount", "sales", "revenue", "net_amount", "المجموع"],
        "unit_price": ["price_per_unit", "unit_price", "price", "rate"],
        "quantity": ["quantity", "qty", "count", "الكمية"],
        "profit": ["profit", "margin", "gain"]
    }
    mapping = {}
    for col in columns:
        c_low = col.lower().replace(" ", "_")
        for std, hints in schema_hints.items():
            if any(h == c_low or h in c_low for h in hints):
                # Avoid mapping multiple columns to the same key
                if std not in mapping.values():
                    mapping[col] = std
                    break
    return mapping

def generate_insights(df, mapping_overrides=None):
    try:
        m = mapping_overrides if mapping_overrides else {}
        
        def to_float(col_name):
            if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
            s = df[col_name].astype(str)
            # Remove currency and commas properly
            s = s.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(s, errors='coerce').fillna(0.0)

        # 1. Identify Columns
        p_col = m.get("product_name", df.columns[0])
        r_col = m.get("total_amount")
        u_col = m.get("unit_price")
        q_col = m.get("quantity")
        f_col = m.get("profit")

        # 2. Revenue Calculation Logic
        if r_col:
            revenue_data = to_float(r_col)
        elif u_col and q_col:
            revenue_data = to_float(u_col) * to_float(q_col)
        else:
            # Fallback: find first numeric column that isn't ID or Date
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            r_col = [c for c in numeric_cols if "id" not in c.lower() and "date" not in c.lower()]
            revenue_data = df[r_col[0]] if r_col else pd.Series([0.0]*len(df))

        df['calculated_revenue'] = revenue_data
        total_rev = float(revenue_data.sum())
        
        # 3. Profit Calculation Logic
        if f_col and f_col in df.columns:
            total_profit = float(to_float(f_col).sum())
        else:
            total_profit = total_rev * 0.25 # Default 25% if not found

        # 4. Best Seller (Must be text)
        best_seller = "N/A"
        if total_rev > 0:
            best_seller = str(df.groupby(p_col)['calculated_revenue'].sum().idxmax())

        return {
            "revenue": round(total_rev, 2),
            "profit": round(total_profit, 2),
            "margin": round((total_profit/total_rev*100), 2) if total_rev > 0 else 0,
            "best_seller": best_seller,
            "df": df,
            "p_col": p_col,
            "r_col": r_col or "Calculated"
        }
    except Exception as e:
        return {"revenue": 0, "profit": 0, "margin": 0, "best_seller": "Error", "df": df, "err": str(e)}



