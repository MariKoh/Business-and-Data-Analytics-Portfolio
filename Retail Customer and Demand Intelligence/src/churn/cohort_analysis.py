"""
Analysis 2a — Cohort retention. Members grouped by first-purchase month; tracks the
% still purchasing in each subsequent month. Output: retention heatmap + table.
Run:  python -m src.churn.cohort_analysis
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

def main():
    tx = pd.read_parquet(PROC / "model_transactions.parquet")
    tx = tx[tx["member_status"] == "Member"].copy()
    tx["customer_id"] = tx["customer_id"].astype("int64")
    tx["order_month"] = tx["invoice_date"].dt.to_period("M")
    cohort = tx.groupby("customer_id")["order_month"].min().rename("cohort")
    tx = tx.merge(cohort, on="customer_id")
    tx["k"] = (tx["order_month"] - tx["cohort"]).apply(lambda x: x.n)

    counts = tx.groupby(["cohort", "k"])["customer_id"].nunique().unstack(fill_value=0)
    size = counts[0]
    retention = counts.divide(size, axis=0) * 100

    # console + table
    ret = retention.round(1)
    ret.index = ret.index.astype(str)
    TAB.mkdir(parents=True, exist_ok=True)
    ret.to_csv(TAB / "cohort_retention.csv")

    # heatmap (cap at 18 months offset for readability)
    maxk = min(18, retention.columns.max())
    R = retention.loc[:, range(0, maxk + 1)]
    R.index = R.index.astype(str)
    fig, ax = plt.subplots(figsize=(13, 7))
    im = ax.imshow(R.values, cmap="YlGnBu", aspect="auto", vmin=0, vmax=60)
    ax.set_xticks(range(R.shape[1])); ax.set_xticklabels(R.columns, fontsize=8)
    ax.set_yticks(range(R.shape[0])); ax.set_yticklabels(R.index, fontsize=7)
    ax.set_xlabel("Months since first purchase"); ax.set_ylabel("Cohort (first-purchase month)")
    ax.set_title("Member cohort retention (% of cohort active each month)", fontweight="bold")
    for i in range(R.shape[0]):
        for j in range(R.shape[1]):
            v = R.values[i, j]
            if v >= 1:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                        color="white" if v > 30 else "black")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="% active")
    fig.tight_layout(); fig.savefig(FIG / "cohort_retention_heatmap.png", dpi=140)

    m1 = retention[1].mean() if 1 in retention.columns else float("nan")
    m3 = retention[3].mean() if 3 in retention.columns else float("nan")
    m6 = retention[6].mean() if 6 in retention.columns else float("nan")
    print("=== COHORT RETENTION (avg across cohorts) ===")
    print(f"Month 1: {m1:.1f}% | Month 3: {m3:.1f}% | Month 6: {m6:.1f}%")
    print(f"cohorts: {retention.shape[0]} | saved heatmap + reports/tables/cohort_retention.csv")

if __name__ == "__main__":
    main()
