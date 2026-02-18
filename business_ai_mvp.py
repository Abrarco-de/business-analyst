import pandas as pd
import numpy as np


REQUIRED_COLUMNS = [
    "product_name",
    "quantity",
    "unit_price",
    "cost_price"
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.str.lower()
        .str.strip()
        .str.replace(" ", "_")
    )
    return df


def validate_schema(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def process_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = normalize_columns(df)
    validate_schema(df)

    # Type safety
    for col in ["quantity", "unit_price", "cost_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["revenue"] = df["quantity"] * df["unit_price"]
    df["cost"] = df["quantity"] * df["cost_price"]
    df["profit"] = df["revenue"] - df["cost"]

    return df


def generate_metrics(df: pd.DataFrame) -> dict:
    total_revenue = df["revenue"].sum()
    total_cost = df["cost"].sum()
    total_profit = df["profit"].sum()

    gross_margin = (
        (total_profit / total_revenue) * 100
        if total_revenue > 0 else 0
    )

    vat = total_revenue * 0.15  # KSA VAT

    aov = total_revenue / df.shape[0] if df.shape[0] > 0 else 0

    product_perf = (
        df.groupby("product_name")
        .agg({
            "revenue": "sum",
            "profit": "sum",
            "quantity": "sum"
        })
        .sort_values("revenue", ascending=False)
    )

    top_revenue_product = product_perf.index[0]
    top_profit_product = product_perf.sort_values("profit", ascending=False).index[0]

    loss_products = product_perf[product_perf["profit"] < 0]

    revenue_concentration = (
        product_perf["revenue"].iloc[0] / total_revenue * 100
        if total_revenue > 0 else 0
    )

    return {
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "total_profit": round(total_profit, 2),
        "gross_margin": round(gross_margin, 2),
        "vat": round(vat, 2),
        "aov": round(aov, 2),
        "top_revenue_product": top_revenue_product,
        "top_profit_product": top_profit_product,
        "loss_products": loss_products.reset_index(),
        "product_perf": product_perf,
        "revenue_concentration": round(revenue_concentration, 2),
    }
