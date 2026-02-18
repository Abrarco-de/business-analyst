import pandas as pd
import numpy as np
import re

def force_clean_data(df):
    """The 'Laundry' for dirty data."""
    # 1. Strip whitespace from all string columns
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    
    # 2. Fill missing product names with 'Unknown Item'
    for col in df.columns:
        if 'product_name' in col:
            df[col] = df[col].fillna('Unknown Item')
            
    # 3. Standardize text (Title Case) to fix 'electronics' vs 'Electronics'
    df = df.applymap(lambda x: x.title() if isinstance(x, str) else x)
    
    return df

def generate_insights(df):
    # Apply the deep clean first
    df = force_clean_data(df)
    
    # Handle multiple product columns (Category + Sub-Category)
    product_cols = [i for i, col in enumerate(df.columns) if col == 'product_name']
    if len(product_cols) > 1:
        df['combined_product'] = df.iloc[:, product_cols].fillna('General').astype(str).agg(' - '.join, axis=1)
        df = df.drop(df.columns[product_cols], axis=1)
        df['product_name'] = df['combined_product']
    else:
        df = df.loc[:, ~df.columns.duplicated()].copy()

    def get_num(col_name):
        data = df.get(col_name, pd.Series([0.0]*len(df)))
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        
        # ADVANCED: Remove currency symbols, commas, and spaces before converting to number
        if data.dtype == 'object':
            data = data.str.replace(r'[^\d.]', '', regex=True)
            
        return pd.to_numeric(data, errors='coerce').fillna(0.0)

    # Calculation logic
    df['calc_qty'] = get_num("quantity")
    
    # If Revenue is 0 or negative, we fix it
    if "total_amount" in df.columns:
        df['calc_rev'] = get_num("total_amount")
    else:
        df['calc_rev'] = get_num("unit_price") * df['calc_qty']
        
    # Safety: Replace any 0 revenue with 0.01 to avoid division by zero errors
    df['calc_rev'] = df['calc_rev'].replace(0, 0.01)

    if "cost_price" in df.columns:
        df['calc_cost'] = get_num("cost_price") * df['calc_qty']
        is_est = False
    else:
        df['calc_cost'] = df['calc_rev'] * 0.65
        is_est = True
        
    df['calc_profit'] = df['calc_rev'] - df['calc_cost']
    
    # Leaderboard Logic
    name_col = 'product_name'
    if name_col not in df.columns:
        df[name_col] = "Item " + df.index.astype(str)

    best_seller = df.groupby(name_col)['calc_qty'].sum().idxmax()
    most_profitable = df.groupby(name_col)['calc_profit'].sum().idxmax()
    
    return {
        "revenue": round(float(df['calc_rev'].sum()), 2),
        "profit": round(float(df['calc_profit'].sum()), 2),
        "margin": round(float((df['calc_profit'].sum() / df['calc_rev'].sum() * 100)), 2),
        "vat": round(float(df['calc_rev'].sum() * 0.15), 2),
        "best_seller": best_seller,
        "most_profitable": most_profitable,
        "is_estimated": is_est,
        "df": df,
        "name_col": name_col
    }
