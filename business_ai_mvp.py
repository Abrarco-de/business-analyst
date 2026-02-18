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
        
        # --- AGGRESSIVE NUMERIC CLEANING ---
        def clean_and_convert(col_name):
            if col_name not in df.columns: 
                return pd.Series([0.0]*len(df))
            
            # Convert to string, remove currency symbols, commas, and whitespace
            series = df[col_name].astype(str)
            series = series.str.replace(r'[^\d.]', '', regex=True)
            
            # Handle empty strings resulting from cleaning
            series = pd.to_numeric(series, errors='coerce').fillna(0.0)
            return series

        # Get column names from mapping
        prod_col = col_map.get("product_name", df.columns[0])
        rev_col = col_map.get("total_amount", df.columns[1])
        qty_col = col_map.get("quantity", df.columns[2])
        prof_col = col_map.get("cost_price", "None")

        # Calculations
        qty_data = clean_and_convert(qty_col)
        rev_data = clean_and_convert(rev_col)
        
        # If Revenue is 0 but we have Price, calculate it
        if rev_data.sum() == 0 and "unit_price" in col_map:
            price_data = clean_and_convert(col_map["unit_price"])
            rev_data = price_data * qty_data

        df['temp_rev'] = rev_data
        total_rev = float(rev_data.sum())
        
        # Profit Logic
        if prof_col != "None" and prof_col in df.columns:
            total_profit = float(clean_and_convert(prof_col).sum())
        else:
            total_profit = total_rev * 0.35 # Standard 35% margin fallback

        return {
            "revenue": round(total_rev, 2),
            "profit": round(total_profit, 2),
            "margin": round((total_profit/total_rev*100), 2) if total_rev > 0 else 0,
            "best_seller": df.groupby(prod_col)['temp_rev'].sum().idxmax() if total_rev > 0 else "N/A",
            "name_col": prod_col,
            "df": df,
            "raw_rev_check": rev_data.head(5).tolist() # For debugging
        }
    except Exception as e:
        return {"revenue":0, "profit":0, "margin":0, "best_seller":"Error", "df":df, "error": str(e)}
        


