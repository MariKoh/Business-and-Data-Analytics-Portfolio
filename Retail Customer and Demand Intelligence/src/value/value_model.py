"""
Value model — translate the four analysis levers into annual profit (illustrative).

Revenue *bases* are computed from the real artifacts (segments, member status, top-100
SKUs), annualised by the data span. The *uplift* assumptions are explicit and
sensitivity-tested. Everything is in the proxy's GBP and is ILLUSTRATIVE — there is no
COGS in the data, and lost sales are not observable, so these are decision-framing
figures, not the retailer's actuals.

Run:  python -m src.value.value_model
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

# --- ASSUMPTIONS (explicit, sensitivity-tested) ---
MARGIN = 0.35                     # gross margin (sensitivity: 0.25 / 0.35 / 0.45)
RETENTION_LIFT = 0.02             # Protect: +2pp of high-value revenue retained
NONMEMBER_CONV = 0.10             # Loyalty: convert 10% of Non-Member revenue to tracked
NONMEMBER_UPLIFT = 0.05           # ...and lift their spend 5% once tracked/targeted
RESCUE_UPLIFT_PP = 0.12           # Rescue: +12pp incremental return rate vs control (~MDE)
RESCUE_DISCOUNT = 0.30            # one-time reactivation coupon depth
RESCUE_COMEBACK_ORDER = 396.0     # avg comeback basket (GBP, from segment EDA)
GROW_RESPONSE = 0.10              # Grow: 10% respond to cross-sell
GROW_ARPU_UPLIFT = 0.15           # ...and responders spend 15% more
AVAIL_RECOVERED = 0.02            # Availability: recover 2% of top-100 revenue via fewer stockouts
SCENARIO = {"Conservative": 0.5, "Base": 1.0, "Optimistic": 1.5}

def main():
    seg = pd.read_parquet(PROC / "customer_segments.parquet")
    tx = pd.read_parquet(PROC / "model_transactions.parquet")
    sku = pd.read_parquet(PROC / "sku_timeseries.parquet")

    span_years = (tx["invoice_date"].max() - tx["invoice_date"].min()).days / 365.25

    # revenue bases (annualised)
    memrev = tx.groupby("member_status")["revenue"].sum() / span_years
    nonmember_rev = float(memrev.get("Non-Member", 0.0))

    seg_rev = seg.groupby("segment")["monetary"].sum() / span_years   # annual revenue per segment
    seg_n = seg["segment"].value_counts()
    hv_active = float(seg_rev.get("High-value, active", 0.0))
    grow_seg = "Mid-value, active, at-risk"
    grow_rev = float(seg_rev.get(grow_seg, 0.0)); grow_n = int(seg_n.get(grow_seg, 0))
    rescue_seg = "High-value, lapsing, at-risk"
    rescue_n = int(seg_n.get(rescue_seg, 0))
    rescue_value_pp = float(seg_rev.get(rescue_seg, 0.0)) / max(rescue_n, 1)  # annual value/member

    top100 = sku.groupby("stock_code")["revenue"].sum().sort_values(ascending=False).head(100).index
    top100_rev = float(sku[sku["stock_code"].isin(top100)]["revenue"].sum() / span_years)

    def levers(margin, k):
        protect = hv_active * RETENTION_LIFT * k * margin
        loyalty = nonmember_rev * NONMEMBER_CONV * NONMEMBER_UPLIFT * k * margin
        recovered = rescue_n * RESCUE_UPLIFT_PP * k
        rescue_gross = recovered * rescue_value_pp * margin
        rescue_cost = recovered * RESCUE_DISCOUNT * RESCUE_COMEBACK_ORDER
        rescue = rescue_gross - rescue_cost
        grow = grow_n * GROW_RESPONSE * GROW_ARPU_UPLIFT * k * (grow_rev / max(grow_n, 1)) * margin
        avail = top100_rev * AVAIL_RECOVERED * k * margin
        return {"Protect (retention)": protect, "Protect (loyalty conversion)": loyalty,
                "Rescue (win-back, net of coupon)": rescue, "Grow (cross-sell ARPU)": grow,
                "Availability (forecast+stocking)": avail}

    base = levers(MARGIN, 1.0)
    base_total = sum(base.values())

    # scenario range (scale uplift assumptions) and margin sensitivity
    scen_tot = {s: sum(levers(MARGIN, k).values()) for s, k in SCENARIO.items()}
    margin_tot = {f"margin {m:.0%}": sum(levers(m, 1.0).values()) for m in (0.25, 0.35, 0.45)}

    # outputs
    vt = pd.Series(base).round(0).rename("annual_profit_gbp").to_frame()
    vt.to_csv(TAB / "value_model.csv")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    items = list(base.items())
    ax.barh([k for k, _ in items][::-1], [v for _, v in items][::-1], color="#2C6E49")
    ax.set_xlabel("Annual profit impact (GBP, illustrative)")
    ax.set_title(f"Value model — base case ~£{base_total/1e6:.2f}M/yr incremental profit", fontweight="bold")
    for i, (k, v) in enumerate(items[::-1]):
        ax.text(v, i, f" £{v/1e3:.0f}k", va="center", fontsize=8)
    fig.tight_layout(); FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / "value_waterfall.png", dpi=140)

    print("=== VALUE MODEL (annual, illustrative GBP) ===")
    print(f"span={span_years:.2f}y | margin={MARGIN:.0%}")
    for k, v in base.items():
        print(f"  {k:38s} £{v:>12,.0f}")
    print(f"  {'TOTAL (base case)':38s} £{base_total:>12,.0f}")
    print("\nScenario range (scale uplifts):")
    for s, v in scen_tot.items():
        print(f"  {s:14s} £{v:>12,.0f}")
    print("\nMargin sensitivity (total):")
    for s, v in margin_tot.items():
        print(f"  {s:14s} £{v:>12,.0f}")
    print("saved -> value_waterfall.png, reports/tables/value_model.csv")
    return base, base_total, scen_tot, margin_tot, dict(span_years=span_years, hv_active=hv_active,
            nonmember_rev=nonmember_rev, grow_rev=grow_rev, grow_n=grow_n, rescue_n=rescue_n,
            rescue_value_pp=rescue_value_pp, top100_rev=top100_rev)

if __name__ == "__main__":
    main()
