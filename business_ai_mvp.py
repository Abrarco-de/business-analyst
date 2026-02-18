def generate_insights(df):
    # 1. HANDLE MULTIPLE PRODUCT COLUMNS (Category + Sub-Category)
    # If the user has multiple columns mapped to 'product_name', combine them!
    product_cols = [i for i, col in enumerate(df.columns) if col == 'product_name']
    
    if len(product_cols) > 1:
        # Combine Category and Sub-Category: "Electronics - Smartphones"
        df['combined_product'] = df.iloc[:, product_cols].fillna('').astype(str).agg(' - '.join, axis=1)
        # Remove the old duplicate columns and set our new one as the primary
        df = df.drop(df.columns[product_cols], axis=1)
        df['product_name'] = df['combined_product']
    else:
        # If only one exists, just ensure it's a single Series
        df = df.loc[:, ~df.columns.duplicated()].copy()

    def get_num(col_name):
        data = df.get(col_name, pd.Series([0.0]*len(df)))
        # Safety: If it's still a DataFrame (2D), force it to Series (1D)
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        return pd.to_numeric(data, errors='coerce').fillna(0.0)

    # 2. CALCULATION LOGIC
    df['calc_qty'] = get_num("quantity")
    
    if "total_amount" in df.columns:
        df['calc_rev'] = get_num("total_amount")
    else:
        df['calc_rev'] = get_num("unit_price") * df['calc_qty']
    
    if "cost_price" in df.columns:
        df['calc_cost'] = get_num("cost_price") * df['calc_qty']
        is_est = False
    else:
        df['calc_cost'] = df['calc_rev'] * 0.65
        is_est = True
        
    df['calc_profit'] = df['calc_rev'] - df['calc_cost']
    
    # 3. LEADERBOARD LOGIC
    name_col = 'product_name' # Now guaranteed to be 1-dimensional
    
    # Best Seller by Volume
    best_seller = df.groupby(name_col)['calc_qty'].sum().idxmax()
    # Most Profitable by Value
    most_profitable = df.groupby(name_col)['calc_profit'].sum().idxmax()
    
    return {
        "revenue": round(float(df['calc_rev'].sum()), 2),
        "profit": round(float(df['calc_profit'].sum()), 2),
        "margin": round(float((df['calc_profit'].sum() / df['calc_rev'].sum() * 100)), 2) if df['calc_rev'].sum() > 0 else 0,
        "vat": round(float(df['calc_rev'].sum() * 0.15), 2),
        "best_seller": best_seller,
        "most_profitable": most_profitable,
        "is_estimated": is_est,
        "df": df,
        "name_col": name_col
    }
