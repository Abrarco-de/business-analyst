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

def generate_insights(df, mapping_overrides=None):
    try:
        col_map = mapping_overrides if mapping_overrides else {}
        
        # --- ULTRA-AGGRESSIVE CLEANING ---
        def clean_and_convert(col_name):
            if col_name not in df.columns: return pd.Series([0.0]*len(df))
            
            # Convert to string and force a standard format
            series = df[col_name].astype(str).str.strip()
            
            # 1. Remove currency symbols and common text
            series = series.str.replace(r'[SAR|INR|USD|\$|€|£]', '', regex=True, case=False)
            
            # 2. Handle European/Indian formatting (1.000,00 -> 1000.00)
            # If there is a comma and a dot, remove the comma
            if series.str.contains(r',.*\.').any():
                series = series.str.replace(',', '')
            # If there is only a comma and it's near the end, treat as decimal
            elif series.str.contains(r',\d{2}$').any():
                series = series.str.replace(',', '.')
            
            # 3. Remove everything except numbers and dots
            series = series.str.replace(r'[^\d.]', '', regex=True)
            
            # 4. Final conversion
            numeric_series = pd.to_numeric(series, errors='coerce').fillna(0.0)
            return numeric_series

        # Pick columns
        prod_col = col_map.get("product_name", df.columns[0])
        rev_col = col_map.get("total_amount", df.columns[1])
        
        # Execute Math
        rev_data = clean_and_convert(rev_col)
        df['temp_rev'] = rev_data
        total_rev = float(rev_data.sum())
        
        # Profit logic (User column or 35%)
        prof_col = col_map.get("cost_price", "None")
        if prof_col != "None" and prof_col in df.columns:
            total_profit = float(clean_and_convert(prof_col).sum())
        else:
            total_profit = total_rev * 0.35

        # Best Seller (Pick name, not ID)
        best_seller = "N/A"
        if total_rev > 0:
            grouped = df.groupby(prod_col)['temp_rev'].sum()
            best_seller = str(grouped.idxmax())

        return {
            "revenue": round(total_rev, 2),
            "profit": round(total_profit, 2),
            "margin": round((total_profit/total_rev*100), 2) if total_rev > 0 else 0,
            "best_seller": best_seller,
            "name_col": prod_col,
            "df": df
        }
    except Exception:
        return {"revenue":0, "profit":0, "margin":0, "best_seller":"Error", "df":df}



