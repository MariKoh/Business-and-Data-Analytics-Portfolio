"""
Business-facing segment visuals (Analysis 1).
Reads reports/tables/segment_profile.csv and renders a two-panel overview:
  A) revenue share by segment (where the money is)
  B) value map: avg recency (x) vs avg spend (y), bubble size = members,
     colour = churn probability -> the rescue opportunity pops out.
Run:  python -m src.segmentation.plot_segments
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"

CHARCOAL = "#2C2C2C"

def main():
    p = pd.read_csv(TAB / "segment_profile.csv")
    p = p.sort_values("revenue_pct", ascending=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.6))

    # Panel A: revenue share
    bars = ax1.barh(p["segment"], p["revenue_pct"], color="#2C6E49")
    ax1.invert_yaxis()
    ax1.set_xlabel("% of revenue")
    ax1.set_title("Where the revenue sits", fontweight="bold")
    for b, v, m in zip(bars, p["revenue_pct"], p["members_pct"]):
        ax1.text(v + 0.7, b.get_y() + b.get_height()/2,
                 f"{v:.1f}%  ({m:.0f}% of members)", va="center", fontsize=9)
    ax1.set_xlim(0, max(p["revenue_pct"]) * 1.25)

    # Panel B: value map
    sizes = (p["members"] / p["members"].max() * 1800) + 120
    sc = ax2.scatter(p["recency_days"], p["monetary"], s=sizes,
                     c=p["churn_prob"], cmap="RdYlGn_r", vmin=0, vmax=1,
                     edgecolor=CHARCOAL, linewidth=1.2, alpha=0.85)
    for _, r in p.iterrows():
        ax2.annotate(r["segment"].split(" (")[0],
                     (r["recency_days"], r["monetary"]),
                     textcoords="offset points", xytext=(8, 8), fontsize=9, fontweight="bold")
    ax2.set_xlabel("Avg recency (days since last purchase) -> staler")
    ax2.set_ylabel("Avg spend per member (GBP)")
    ax2.set_title("Value map  (bubble = members, colour = churn risk)", fontweight="bold")
    cbar = fig.colorbar(sc, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label("churn probability")

    fig.suptitle("Customer segments — business overview", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG / "seg_business_overview.png"
    fig.savefig(out, dpi=140)
    print("saved ->", out.relative_to(ROOT))

if __name__ == "__main__":
    main()
