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
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except: return None

def get_header_mapping(columns):
    schema_hints = {
        "product_name": ["product", "category", "sub_category", "item", "المنتج"],
        "total_amount": ["total_amount", "sales", "revenue", "net_amount"],
        "unit_price": ["price_per_unit", "unit_price", "price", "rate"],
        "quantity": ["quantity", "qty", "count"],
        "profit": ["profit", "margin", "gain", "الربح"]
    }
    mapping = {}
    for col in columns:
        c_low = col.lower().replace(" ", "_")
        for std, hints in schema_hints.items():
            if any(h == c_low or h in c_low for h in hints):
                if std not in mapping.values():
                    mapping[col] = std
                    break
    return mapping

def generate_insights(df, mapping_overrides=None):
    try:
        m = mapping_overrides if mapping_overrides else {}
        
        def to_float(col_name):
            if not col_name or col_name not in df.columns: return pd.Series([0.0]*len(df))
            s = df[col_name].astype(str).str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(s, errors='coerce').fillna(0.0)

        p_col = m.get("product_name", df.columns[0])
        r_col = m.get("total_amount")
        u_col = m.get("unit_price")
        q_col = m.get("quantity")
        f_col = m.get("profit")

        # Revenue Logic
        if r_col:
            rev_series = to_float(r_col)
        elif u_col and q_col:
            rev_series = to_float(u_col) * to_float(q_col)
        else:
            rev_series = pd.Series([0.0]*len(df))

        df['calculated_revenue'] = rev_series
        total_rev = float(rev_series.sum())
        
        # ZATCA VAT (15%)
        zatca_vat = total_rev * 0.15

        # Profit Logic
        if f_col and f_col in df.columns:
            profit_series = to_float(f_col)
        else:
            profit_series = rev_series * 0.25 # Estimate
        
        df['calculated_profit'] = profit_series
        total_profit = float(profit_series.sum())

        # Best Seller (By Revenue) & Highest Profit Product
        best_seller = "N/A"
        most_profitable_prod = "N/A"
        
        if total_rev > 0:
            best_seller = str(df.groupby(p_col)['calculated_revenue'].sum().idxmax())
            most_profitable_prod = str(df.groupby(p_col)['calculated_profit'].sum().idxmax())

        return {
            "revenue": round(total_rev, 2),
            "zatca_vat": round(zatca_vat, 2),
            "profit": round(total_profit, 2),
            "margin": round((total_profit/total_rev*100), 2) if total_rev > 0 else 0,
            "best_seller": best_seller,
            "most_profitable_prod": most_profitable_prod,
            "df": df,
            "p_col": p_col
        }
    except Exception as e:
        return {"revenue": 0, "zatca_vat":0, "profit": 0, "margin": 0, "best_seller": "Error", "df": df}



