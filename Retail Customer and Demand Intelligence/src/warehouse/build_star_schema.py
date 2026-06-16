"""
Phase 2 — Star-schema warehouse. Fact table keyed by surrogate IDs (product_id,
category_id) and natural customer_id, with the REAL date; dimension/master tables map
the IDs to names/attributes. Materialised as parquet (loadable into DuckDB/any DW).

  fact_sales(invoice, date, customer_id, product_id, quantity, price, revenue, member_status)
  dim_customer(customer_id, member_status, segment, churn_prob, recency_days, frequency, monetary)
  dim_product(product_id, stock_code, description, category_id)
  dim_category(category_id, category_name)
  dim_date(date, year, quarter, month, month_name, iso_week, week_start, is_december)

Run:  python -m src.warehouse.build_star_schema
"""
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
WH = ROOT / "data" / "warehouse"

def main():
    tx = pd.read_parquet(PROC / "clean_transactions.parquet")
    tx = tx[tx["is_product"]].copy()
    tx["stock_code"] = tx["stock_code"].astype(str)
    cat = pd.read_csv(PROC / "category_map.csv", dtype={"stock_code": "string"})
    cat["stock_code"] = cat["stock_code"].astype(str)
    cf = pd.read_parquet(PROC / "customer_features.parquet")
    seg = pd.read_parquet(PROC / "customer_segments.parquet")

    # dim_category
    dim_category = (pd.DataFrame({"category_name": sorted(cat["category"].unique())})
                    .reset_index().rename(columns={"index": "category_id"}))
    dim_category["category_id"] += 1
    cat2id = dict(zip(dim_category["category_name"], dim_category["category_id"]))

    # dim_product (surrogate product_id; maps to stock_code + description + category)
    dim_product = cat.rename(columns={"category": "category_name"}).copy()
    dim_product["category_id"] = dim_product["category_name"].map(cat2id)
    dim_product = dim_product.sort_values("stock_code").reset_index(drop=True)
    dim_product.insert(0, "product_id", np.arange(1, len(dim_product) + 1))
    dim_product = dim_product[["product_id", "stock_code", "description", "category_id"]]
    sc2pid = dict(zip(dim_product["stock_code"], dim_product["product_id"]))

    # dim_customer (natural customer_id; key 0 = Non-Member). Members from features + segment.
    seg_attr = seg[["customer_id", "segment", "churn_prob"]]
    dim_customer = cf.merge(seg_attr, on="customer_id", how="left")
    dim_customer["member_status"] = "Member"
    dim_customer = dim_customer[["customer_id", "member_status", "segment", "churn_prob",
                                 "recency_days", "frequency", "monetary"]]
    nonmember = pd.DataFrame([{"customer_id": 0, "member_status": "Non-Member", "segment": "Non-Member",
                               "churn_prob": np.nan, "recency_days": np.nan, "frequency": np.nan,
                               "monetary": np.nan}])
    dim_customer = pd.concat([nonmember, dim_customer], ignore_index=True)
    dim_customer["customer_id"] = dim_customer["customer_id"].astype("int64")

    # fact_sales (IDs + REAL date)
    fact = tx.copy()
    fact["date"] = fact["invoice_date"].dt.normalize()
    fact["product_id"] = fact["stock_code"].map(sc2pid)
    fact["customer_id"] = fact["customer_id"].fillna(0).astype("int64")
    fact["member_status"] = np.where(fact["customer_id"] == 0, "Non-Member", "Member")
    fact_sales = fact[["invoice", "date", "customer_id", "product_id",
                       "quantity", "price", "revenue", "member_status"]]

    # dim_date (REAL date as key)
    d = pd.to_datetime(pd.Series(fact_sales["date"].unique())).sort_values()
    dim_date = pd.DataFrame({"date": d})
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.strftime("%b")
    dim_date["iso_week"] = dim_date["date"].dt.isocalendar().week.astype(int)
    dim_date["week_start"] = dim_date["date"] - pd.to_timedelta(dim_date["date"].dt.weekday, unit="D")
    dim_date["is_december"] = (dim_date["month"] == 12).astype(int)

    WH.mkdir(parents=True, exist_ok=True)
    for name, df in [("fact_sales", fact_sales), ("dim_customer", dim_customer),
                     ("dim_product", dim_product), ("dim_category", dim_category),
                     ("dim_date", dim_date)]:
        df.to_parquet(WH / f"{name}.parquet", index=False)

    # verification: star joins
    fp = fact_sales.merge(dim_product[["product_id", "category_id"]], on="product_id") \
                   .merge(dim_category, on="category_id")
    by_cat = (fp.groupby("category_name")["revenue"].sum().sort_values(ascending=False) / 1e6).round(2)
    fd = fact_sales.merge(dim_date[["date", "year", "month_name", "month"]], on="date")
    by_mon = fd.groupby(["year", "month"])["revenue"].sum()

    print("=== STAR SCHEMA (parquet, data/warehouse/) ===")
    print(f"fact_sales   : {len(fact_sales):>9,} rows")
    print(f"dim_customer : {len(dim_customer):>9,} (incl. key 0 = Non-Member)")
    print(f"dim_product  : {len(dim_product):>9,}")
    print(f"dim_category : {len(dim_category):>9,}")
    print(f"dim_date     : {len(dim_date):>9,} days")
    print(f"\nfact revenue total: GBP {fact_sales['revenue'].sum()/1e6:.2f}M  | unmapped product_id: {fact_sales['product_id'].isna().sum()}")
    print("\nStar join check — revenue (GBP M) by category:")
    print(by_cat.to_string())
    print(f"\nStar join check — months covered: {len(by_mon)}  (fact->dim_date OK)")

if __name__ == "__main__":
    main()
