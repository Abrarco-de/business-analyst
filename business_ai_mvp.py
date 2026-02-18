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
        # Clean hidden characters from headers
        df.columns = [str(c).replace('ï»¿', '').strip() for c in df.columns]
        return df
    except Exception:
        return None

def generate_insights(df, mapping_overrides=None):
    try:
        col_map = mapping_overrides if mapping_overrides else {}
        
        def clean_and_convert(col_name):
            if col_name not in df.columns: return pd.Series([0.0]*len(df))
            series = df[col_name].astype(str).str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(series, errors='coerce').fillna(0.0)

        # 1. Map Columns
        prod_col = col_map.get("product_name", df.columns[0])
        rev_col = col_map.get("total_amount", df.columns[1])
        
        # 2. Clean numeric data
        rev_data = clean_and_convert(rev_col)
        df['temp_rev'] = rev_data
        total_rev = float(rev_data.sum())
        
        # 3. Profit Logic
        prof_col = col_map.get("cost_price", "None")
        if prof_col != "None" and prof_col in df.columns:
            total_profit = float(clean_and_convert(prof_col).sum())
        else:
            total_profit = total_rev * 0.35

        # 4. Best Seller Logic (Ensures it returns the Name, not a number)
        best_seller = "N/A"
        if total_rev > 0 and prod_col in df.columns:
            # We group and sum, then find the index (the name)
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


