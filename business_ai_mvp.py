import pandas as pd

# ---------- COLUMN ALIASES ----------
COLUMN_MAP = {
    "product_name": ["product", "item", "item_name", "menu_item", "description", "name"],
    "quantity": ["qty", "quantity", "units", "count"],
    "unit_price": ["price", "unit_price", "rate"],
    "sales": ["sales", "revenue", "total_sales", "amount"],
    "profit": ["profit", "net_profit", "margin_value"],
    "discount": ["discount", "discount_amount"],
}

# ---------- UTIL ----------
def find_column(df, aliases):
    for col in df.columns:
        if col.lower().strip() in aliases:
            return col
    return None

# ---------- CORE ----------
def process_business_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = [c.lower().strip() for c in df.columns]

    schema = {}
    for standard, aliases in COLUMN_MAP.items():
        found = find_column(df, aliases)
        if found:
            schema[standard] = found

    df = df.rename(columns={v: k for k, v in schema.items()})

    if "product_name" not in df:
        df["product_name"] = "Unknown Item"

    return df

# ---------- ANALYTICS ----------
def generate_insights(df):
    # ---------- CASE 1: POS already gives sales + profit ----------
    if "sales" in df.columns and "profit" in df.columns:
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce").fillna(0)
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)
        df["discount"] = pd.to_numeric(df.get("discount", 0), errors="coerce").fillna(0)

        total_revenue = round(df["sales"].sum(), 2)
        total_profit = round(df["profit"].sum(), 2)
        margin = round((total_profit / total_revenue * 100), 2) if total_revenue else 0

    # ---------- CASE 2: Need to calculate ----------
    elif "unit_price" in df.columns and "quantity" in df.columns:
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        df["sales"] = df["unit_price"] * df["quantity"]
        df["profit"] = df["sales"]  # cost unknown

        total_revenue = round(df["sales"].sum(), 2)
        total_profit = round(df["profit"].sum(), 2)
        margin = 0

    else:
        raise ValueError(
            "File must contain either (sales + profit) OR (price + quantity)"
        )

    vat = round(total_revenue * 0.15, 2)

    top_products = (
        df.groupby("product_name")["profit"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    loss_products = (
        df.groupby("product_name")["profit"]
        .sum()
        .sort_values()
        .head(5)
        .reset_index()
    )

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "margin": margin,
        "vat": vat,
        "top_products": top_products,
        "loss_products": loss_products,
    }



