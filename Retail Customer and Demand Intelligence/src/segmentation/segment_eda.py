"""
Per-segment behavioural EDA (Analysis 1 deep-dive).
Profiles each segment beyond RFMTC means: basket habits, cadence, repeat rate,
price point, and category spend mix. Outputs a narrative-ready report + heatmap.
Run:  python -m src.segmentation.segment_eda
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

def main():
    seg = pd.read_parquet(PROC / "customer_segments.parquet")
    cf = pd.read_parquet(PROC / "customer_features.parquet")
    tx = pd.read_parquet(PROC / "model_transactions.parquet")
    cat = pd.read_csv(PROC / "category_map.csv", dtype={"stock_code": "string"})

    for d in (seg, cf):
        d["customer_id"] = d["customer_id"].astype("int64")
    tx["customer_id"] = tx["customer_id"].astype("int64")
    tx["stock_code"] = tx["stock_code"].astype("string")

    m = seg.merge(cf[["customer_id", "avg_basket_value", "avg_items_per_basket",
                      "num_distinct_skus", "first_purchase", "last_purchase"]],
                  on="customer_id", how="left")
    span = (m["last_purchase"] - m["first_purchase"]).dt.days
    m["cadence_days"] = np.where(m["frequency"] > 1, span / (m["frequency"] - 1), np.nan)
    m["repeat"] = (m["frequency"] > 1).astype(int)

    order = m.groupby("segment")["monetary"].mean().sort_values(ascending=False).index.tolist()

    prof = m.groupby("segment").agg(
        members=("customer_id", "size"),
        avg_spend=("monetary", "mean"),
        avg_freq=("frequency", "mean"),
        recency_days=("recency_days", "mean"),
        tenure_days=("tenure_days", "mean"),
        basket_value=("avg_basket_value", "mean"),
        items_per_basket=("avg_items_per_basket", "mean"),
        distinct_skus=("num_distinct_skus", "mean"),
        pct_repeat=("repeat", "mean"),
        cadence_days=("cadence_days", "median"),
        churn=("churn_prob", "mean"),
    ).reindex(order).round(1)
    prof["pct_repeat"] = (prof["pct_repeat"] * 100).round(0)

    # category spend mix: segment x category (% of segment revenue)
    txm = tx.merge(seg[["customer_id", "segment"]], on="customer_id", how="inner")
    txm = txm.merge(cat[["stock_code", "category"]], on="stock_code", how="left")
    txm["category"] = txm["category"].fillna("Other")
    txm["unit_price"] = txm["revenue"] / txm["quantity"].clip(lower=1)

    avg_price = txm.groupby("segment")["unit_price"].mean().round(2)
    prof["avg_unit_price"] = avg_price.reindex(order).values

    mix = txm.pivot_table(index="segment", columns="category", values="revenue",
                          aggfunc="sum", fill_value=0).reindex(order)
    mix_pct = (mix.div(mix.sum(axis=1), axis=0) * 100).round(1)

    # top-3 categories per segment
    top_cats = {}
    for s in order:
        top_cats[s] = ", ".join(f"{c} {mix_pct.loc[s, c]:.0f}%"
                                for c in mix_pct.loc[s].sort_values(ascending=False).head(3).index)

    TAB.mkdir(parents=True, exist_ok=True)
    prof.to_csv(TAB / "segment_behaviour.csv")
    mix_pct.to_csv(TAB / "segment_category_mix.csv")

    # heatmap
    cols = mix_pct.sum().sort_values(ascending=False).index
    M = mix_pct[cols]
    fig, ax = plt.subplots(figsize=(12, 5.2))
    im = ax.imshow(M.values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(M.index))); ax.set_yticklabels(M.index, fontsize=9)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            if v >= 4:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if v > M.values.max()*0.5 else "black")
    ax.set_title("Category spend mix by segment (% of segment revenue)", fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="% of spend")
    fig.tight_layout()
    fig.savefig(FIG / "seg_category_heatmap.png", dpi=140)

    # report
    parts = ["# Per-Segment Behavioural EDA (Analysis 1 deep-dive)\n",
             "Behaviour beyond RFMTC means — basket habits, cadence, repeat rate, price "
             "point, and category spend mix. Source: model_transactions + customer_features "
             "+ category_map.\n\n## Behavioural profile\n",
             "```\n" + prof.to_string() + "\n```\n",
             "\n## Top categories per segment\n"]
    for s in order:
        parts.append(f"- **{s}** — {top_cats[s]}\n")
    parts.append("\nFull matrix: `reports/tables/segment_category_mix.csv` | "
                 "heatmap: `reports/figures/seg_category_heatmap.png`\n")
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "segment_eda.md").write_text("".join(parts), encoding="utf-8")

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("=== BEHAVIOURAL PROFILE ===")
    print(prof.to_string())
    print("\n=== TOP CATEGORIES PER SEGMENT ===")
    for s in order:
        print(f"  {s:32s} -> {top_cats[s]}")
    print("\nsaved -> docs/segment_eda.md, seg_category_heatmap.png, 2 tables")

if __name__ == "__main__":
    main()
