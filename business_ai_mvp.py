 import pandas as pd
import numpy as np

# -----------------------------
# Load & clean business data
# -----------------------------
def process_business_file(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    required = ["product_name", "quantity", "unit_price", "cost_price"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0)
    df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce").fillna(0)

    return df


# -----------------------------
# Business analytics engine
# -----------------------------
def generate_insights(df):
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["cost"] = df["quantity"] * df["cost_price"]
    df["profit"] = df["revenue"] - df["cost"]

    total_revenue = round(df["revenue"].sum(), 2)
    total_profit = round(df["profit"].sum(), 2)
    margin = round((total_profit / total_revenue) * 100, 2) if total_revenue else 0

    vat = round(total_revenue * 0.15, 2)

    top_products = (
        df.groupby("product_name")["profit"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    loss_products = (
        df.groupby("product_name")["profit"]
        .sum()
        .sort_values()
        .head(5)
    )

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "margin": margin,
        "vat": vat,
        "top_products": top_products,
        "loss_products": loss_products,
    }


