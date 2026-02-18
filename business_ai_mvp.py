import pandas as pd

# ---------- COLUMN ALIASES ----------
COLUMN_MAP = {
    "product_name": ["product", "item", "item_name", "product_name", "menu_item", "description", "name"],
    "quantity": ["qty", "quantity", "count", "units", "sold_qty"],
    "unit_price": ["price", "unit_price", "selling_price", "rate", "amount"],
    "cost_price": ["cost", "cost_price", "buy_price", "purchase_price"],
    "timestamp": ["date", "time", "timestamp", "created_at", "sale_date"]
}

# ---------- UTIL ----------
def find_column(df, possible_names):
    for col in df.columns:
        if col.lower().strip() in possible_names:
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

    if "unit_price" not in schema or "quantity" not in schema:
        raise ValueError("File must contain at least price and quantity columns")

    df = df.rename(columns={v: k for k, v in schema.items()})

    # Defaults if missing
    if "product_name" not in df:
        df["product_name"] = "Unknown Item"

    if "cost_price" not in df:
        df["cost_price"] = 0

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)
    df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce").fillna(0)

    return df

# ---------- ANALYTICS ----------
def generate_insights(df):
    df["revenue"] = df["unit_price"] * df["quantity"]
    df["cost"] = df["cost_price"] * df["quantity"]
    df["profit"] = df["revenue"] - df["cost"]

    total_revenue = round(df["revenue"].sum(), 2)
    total_profit = round(df["profit"].sum(), 2)
    margin = round((total_profit / total_revenue * 100), 2) if total_revenue else 0
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



