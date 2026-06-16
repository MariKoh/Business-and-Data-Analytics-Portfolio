"""
Analysis 3 — Cross-sell (item affinity + item-based collaborative filtering) and
dead-stock bundling. Powers the Grow play (next-best-product) and inventory clearance.

  * Affinity rules: pairwise lift/confidence from basket co-occurrence (top bundles).
  * Item-based CF: cosine similarity on the basket x item matrix -> "also-bought"
    recommender, evaluated by leave-one-out hit-rate@K (an honest quality metric).
  * Dead-stock bundling: slowest movers paired with a high-affinity popular anchor
    (or a same-category bestseller) to clear inventory.

Scalable (scipy sparse). Baskets are guest-inclusive (basket_transactions).
Run:  python -m src.basket.cross_sell
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
MIN_BASKETS = 10      # an item must appear in >= this many baskets to be modelled
MIN_PAIR = 20         # a pair must co-occur in >= this many baskets to be a rule
TOPK = 10
rng = np.random.default_rng(42)

def label(stock, desc_map):
    d = desc_map.get(stock, "")
    return f"{stock} {str(d)[:28]}"

def main():
    baskets = pd.read_parquet(PROC / "basket_transactions.parquet")
    master = pd.read_parquet(PROC / "product_master.parquet")
    desc_map = dict(zip(master["stock_code"].astype(str), master["description"]))
    cat_map = dict(zip(master["stock_code"].astype(str), master["category"]))

    ex = baskets[["invoice", "items"]].explode("items").dropna()
    ex["items"] = ex["items"].astype(str)
    counts = ex["items"].value_counts()
    keep = counts[counts >= MIN_BASKETS].index
    idx = {it: i for i, it in enumerate(keep)}
    items = list(keep)
    n_items = len(items)

    exk = ex[ex["items"].isin(idx)].copy()
    brow = {inv: r for r, inv in enumerate(baskets["invoice"].astype(str))}
    exk["r"] = exk["invoice"].astype(str).map(brow)
    exk["c"] = exk["items"].map(idx)
    n_b = len(baskets)
    X = sparse.csr_matrix((np.ones(len(exk)), (exk["r"], exk["c"])), shape=(n_b, n_items))
    X.data[:] = 1.0
    item_freq = np.asarray(X.sum(axis=0)).ravel()

    # --- affinity rules (lift) ---
    C = (X.T @ X).tocoo()
    rules = []
    for i, j, co in zip(C.row, C.col, C.data):
        if i < j and co >= MIN_PAIR:
            lift = n_b * co / (item_freq[i] * item_freq[j])
            rules.append((items[i], items[j], int(co), co / item_freq[i], co / item_freq[j], lift))
    rdf = pd.DataFrame(rules, columns=["item_a", "item_b", "co_baskets", "conf_a_to_b", "conf_b_to_a", "lift"])
    rdf = rdf.sort_values("lift", ascending=False).reset_index(drop=True)
    rdf["a"] = rdf["item_a"].map(lambda s: label(s, desc_map))
    rdf["b"] = rdf["item_b"].map(lambda s: label(s, desc_map))
    rdf.to_csv(TAB / "cross_sell_rules.csv", index=False)

    # --- item-based CF (cosine) ---
    sim = cosine_similarity(X.T, dense_output=True)
    np.fill_diagonal(sim, 0.0)

    # leave-one-out hit-rate@K on a sample of multi-item baskets
    multi = exk.groupby("r")["c"].apply(list)
    multi = multi[multi.apply(len) >= 2]
    samp = multi.sample(min(1500, len(multi)), random_state=42)
    hits = 0
    for cidxs in samp:
        cidxs = list(cidxs)
        held = rng.choice(cidxs)
        ctx = [c for c in cidxs if c != held]
        scores = sim[:, ctx].sum(axis=1)
        scores[ctx] = -1
        topk = np.argpartition(scores, -TOPK)[-TOPK:]
        if held in topk:
            hits += 1
    hit_rate = hits / len(samp)

    # --- dead-stock bundling ---
    sku = pd.read_parquet(PROC / "sku_timeseries.parquet")
    units = sku.groupby("stock_code")["quantity"].sum()
    thresh = units.quantile(0.10)
    slow = units[units <= thresh].sort_values().head(15)
    bundles = []
    for s in slow.index:
        s = str(s)
        anchor, reason = None, None
        if s in idx:  # use co-occurrence anchor
            row = sim[idx[s]]
            if row.max() > 0:
                anchor = items[int(row.argmax())]; reason = "high co-purchase affinity"
        if anchor is None:  # fallback: category bestseller
            c = cat_map.get(s, "Other")
            same = [it for it in items if cat_map.get(it) == c]
            if same:
                anchor = max(same, key=lambda it: item_freq[idx[it]]); reason = f"bestseller in {c}"
        bundles.append((label(s, desc_map), int(units[s]), label(anchor, desc_map) if anchor else "-", reason or "-"))
    bdf = pd.DataFrame(bundles, columns=["slow_mover", "units_sold", "suggested_anchor", "reason"])
    bdf.to_csv(TAB / "deadstock_bundles.csv", index=False)

    # --- figure: top bundles by lift ---
    top = rdf.head(12)[::-1]
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(range(len(top)), top["lift"], color="#2C6E49")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"{a.split(' ',1)[1]}  +  {b.split(' ',1)[1]}" for a, b in zip(top["a"], top["b"])], fontsize=7)
    ax.set_xlabel("lift"); ax.set_title("Top cross-sell bundles by lift", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "cross_sell_top_bundles.png", dpi=140)

    print(f"=== CROSS-SELL (items>= {MIN_BASKETS} baskets: {n_items} | baskets: {n_b:,}) ===")
    print(f"affinity rules (pairs co-occurring >= {MIN_PAIR}): {len(rdf):,}")
    print(f"item-based CF hit-rate@{TOPK}: {hit_rate:.1%}  (random baseline ~ {TOPK/n_items:.2%})")
    print("\nTop 5 cross-sell bundles by lift:")
    for _, r in rdf.head(5).iterrows():
        print(f"  lift {r.lift:5.1f} | {r.a}  +  {r.b}  (co={r.co_baskets})")
    print("\nDead-stock bundle suggestions (sample):")
    for _, r in bdf.head(5).iterrows():
        print(f"  {r.slow_mover} (sold {r.units_sold}) -> {r.suggested_anchor}  [{r.reason}]")
    print("\nsaved -> cross_sell_rules.csv, deadstock_bundles.csv, cross_sell_top_bundles.png")

if __name__ == "__main__":
    main()
