def generate_insights(df):
    try:
        # --- 1. Data Cleaning ---
        # Keep only the first of any duplicate columns
        df = df.loc[:, ~df.columns.duplicated()].copy()

        def get_num(col_name):
            series = df.get(col_name, pd.Series([0.0]*len(df)))
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            return pd.to_numeric(series, errors='coerce').fillna(0.0)

        # --- 2. Calculations ---
        calc_qty = get_num("quantity")
        
        if "total_amount" in df.columns:
            calc_rev = get_num("total_amount")
        else:
            calc_rev = get_num("unit_price") * calc_qty
        
        # Avoid empty dataset errors
        total_rev = float(calc_rev.sum())
        
        # --- 3. The Result Dictionary ---
        # Important: Ensure this is INSIDE the try block
        res = {
            "revenue": round(total_rev, 2),
            "profit": round(total_rev * 0.35, 2), # Default 35% margin if cost missing
            "margin": 35.0,
            "vat": round(total_rev * 0.15, 2),
            "best_seller": "N/A",
            "most_profitable": "N/A",
            "is_estimated": True,
            "df": df,
            "name_col": df.columns[0]
        }
        
        # Try to get real product names if they exist
        if "product_name" in df.columns:
            df['calc_rev'] = calc_rev
            res['name_col'] = "product_name"
            res['best_seller'] = df.groupby("product_name")['calc_rev'].sum().idxmax()

        return res # <--- SUCCESS RETURN

    except Exception as e:
        # --- 4. THE SAFETY NET ---
        # If anything fails, return a 'Zero' dictionary instead of None
        print(f"Error in insights: {e}")
        return {
            "revenue": 0.0,
            "profit": 0.0,
            "margin": 0.0,
            "vat": 0.0,
            "best_seller": "Error in data",
            "most_profitable": "Error in data",
            "is_estimated": True,
            "df": df,
            "name_col": df.columns[0] if not df.empty else "None"
        }
