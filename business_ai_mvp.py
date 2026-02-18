import pandas as pd
import numpy as np
import google.generativeai as genai
import re

def configure_ai(api_key):
    if api_key:
        try:
            # This forces the stable v1 API version
            import os
            os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"
            genai.configure(api_key=api_key, transport='rest') 
            return True
        except:
            return False
    return False

def process_business_file(uploaded_file):
    """Safely loads CSV or Excel files."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        # Remove duplicate columns immediately
        df = df.loc[:, ~df.columns.duplicated()].copy()
        return df
    except:
        return pd.DataFrame() # Return empty instead of None

def get_header_mapping(columns):
    standard_schema = {
        # Added 'category' and 'sub' here to catch your specific columns
        "product_name": ["item", "product", "category", "sub", "المنتج", "الصنف", "type", "description"],
        "unit_price": ["price per unit", "unit price", "rate", "سعر الوحدة", "price", "unit_price"],
        "quantity": ["qty", "quantity", "count", "الكمية", "units", "amount"],
        "total_amount": ["total amount", "total sales", "net amount", "المجموع", "total", "sales", "revenue"],
        "cost_price": ["unit cost", "cost price", "purchase", "التكلفة", "cost"]
    }
    mapping = {}
    for col in columns:
        col_l = str(col).lower().strip().replace(" ", "_") # Clean the column name
        for std, hints in standard_schema.items():
            if any(h in col_l for h in hints):
                mapping[col] = std
                break
    return mapping
def generate_insights(df):
    """The engine that cleans and analyzes everything."""
    try:
        # Handle Category + Sub-Category
        prod_cols = [i for i, col in enumerate(df.columns) if col == 'product_name']
        if len(prod_cols) > 1:
            df['product_name_final'] = df.iloc[:, prod_cols].fillna('General').astype(str).agg(' - '.join, axis=1)
            df = df.drop(df.columns[prod_cols], axis=1)
            df['product_name'] = df['product_name_final']
        else:
            df = df.loc[:, ~df.columns.duplicated()].copy()

        # Helper to clean currency and convert to float
        def to_num(col_name):
            data = df.get(col_name, pd.Series([0.0]*len(df)))
            if isinstance(data, pd.DataFrame): data = data.iloc[:, 0]
            if data.dtype == 'object':
                data = data.str.replace(r'[^\d.]', '', regex=True)
            return pd.to_numeric(data, errors='coerce').fillna(0.0)

        df['calc_qty'] = to_num("quantity")
        if "total_amount" in df.columns:
            df['calc_rev'] = to_num("total_amount")
        else:
            df['calc_rev'] = to_num("unit_price") * df['calc_qty']

        # Financial Calculations
        rev = float(df['calc_rev'].sum())
        vat = rev * 0.15
        
        if "cost_price" in df.columns:
            df['calc_cost'] = to_num("cost_price") * df['calc_qty']
            is_est = False
        else:
            df['calc_cost'] = df['calc_rev'] * 0.65 # 65% default cost
            is_est = True

        profit = float(df['calc_rev'].sum() - df['calc_cost'].sum())
        margin = (profit / rev * 100) if rev > 0 else 0

        # Leaderboard
        name_col = 'product_name' if 'product_name' in df.columns else df.columns[0]
        best_seller = df.groupby(name_col)['calc_qty'].sum().idxmax() if not df.empty else "N/A"
        most_profitable = df.groupby(name_col)['calc_rev'].sum().idxmax() if not df.empty else "N/A"

        return {
            "revenue": round(rev, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 2),
            "vat": round(vat, 2),
            "best_seller": best_seller,
            "most_profitable": most_profitable,
            "is_estimated": is_est,
            "df": df,
            "name_col": name_col
        }
    except Exception as e:
        return {"revenue": 0, "profit": 0, "margin": 0, "vat": 0, "best_seller": "Error", "most_profitable": "Error", "is_estimated": True, "df": df, "name_col": "N/A"}


