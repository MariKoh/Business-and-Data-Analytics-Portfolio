"""
Analysis 1 — Customer segmentation by purchasing behaviour (RFMTC).

Business question: which customer groups carry the most profit potential, so the
business can concentrate retention and growth spend where it pays back?

Technique (business leads, tech serves):
  * Features = RFMTC — Recency, Frequency, Monetary, Time (tenure), Churn-probability.
    - R, F, M, T come from the customer feature mart.
    - C (churn probability) = 1 - P(alive) from a BG/NBD probability model, the
      principled "alive" estimate for non-contractual retail. It also seeds CLV later.
  * K-Means with k chosen by elbow + silhouette + business interpretability.
  * Profile every segment, then rank the top 3 by PROFIT POTENTIAL.

Outputs:
  data/processed/customer_segments.parquet   (customer_id, cluster, segment, features)
  reports/tables/segment_profile.csv
  reports/figures/seg_elbow_silhouette.png
  reports/figures/seg_pca_scatter.png

Run:  python -m src.segmentation.run_segmentation
"""
from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from lifetimes import BetaGeoFitter
from lifetimes.utils import summary_data_from_transaction_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("segmentation")

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

K_RANGE = range(2, 11)
K_BUSINESS_WINDOW = (6, 8)  # Retailer has marketing capacity for finer segments
RANDOM_STATE = 42


def build_churn_probability(tx: pd.DataFrame) -> pd.DataFrame:
    """C of RFMTC: churn probability = 1 - P(alive), from a BG/NBD model."""
    obs_end = tx["invoice_date"].max()
    summ = summary_data_from_transaction_data(
        tx, customer_id_col="customer_id", datetime_col="invoice_date",
        monetary_value_col="revenue", observation_period_end=obs_end, freq="D",
    )
    bgf = BetaGeoFitter(penalizer_coef=1e-3)
    bgf.fit(summ["frequency"], summ["recency"], summ["T"])
    p_alive = np.asarray(bgf.conditional_probability_alive(summ["frequency"], summ["recency"], summ["T"]))
    out = pd.DataFrame({"customer_id": summ.index.astype("int64"),
                        "p_alive": p_alive,
                        "churn_prob": 1.0 - p_alive})
    log.info("BG/NBD fitted on %d customers | mean P(alive)=%.3f", len(out), out["p_alive"].mean())
    return out


def assemble_rfmtc() -> pd.DataFrame:
    cf = pd.read_parquet(PROC / "customer_features.parquet")
    tx = pd.read_parquet(PROC / "model_transactions.parquet")
    tx = tx[tx["customer_id"].notna() & (tx["revenue"] > 0)].copy()
    tx["customer_id"] = tx["customer_id"].astype("int64")

    churn = build_churn_probability(tx)
    df = cf.merge(churn, on="customer_id", how="left")
    df["churn_prob"] = df["churn_prob"].fillna(df["churn_prob"].median())
    df["p_alive"] = df["p_alive"].fillna(df["p_alive"].median())

    # RFMTC feature frame (transformed for clustering)
    feat = pd.DataFrame({
        "R_recency_days": df["recency_days"],
        "F_log_frequency": np.log1p(df["frequency"]),
        "M_log_monetary": np.log1p(df["monetary"].clip(lower=0)),
        "T_tenure_days": df["tenure_days"],
        "C_churn_prob": df["churn_prob"],
    }, index=df.index)
    return df, feat


def choose_k(X: np.ndarray) -> tuple[int, pd.DataFrame]:
    rows = []
    for k in K_RANGE:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(X)
        sil = silhouette_score(X, km.labels_, sample_size=4000, random_state=RANDOM_STATE)
        rows.append({"k": k, "inertia": km.inertia_, "silhouette": sil})
        log.info("k=%d  inertia=%.0f  silhouette=%.3f", k, km.inertia_, sil)
    scan = pd.DataFrame(rows)
    lo, hi = K_BUSINESS_WINDOW
    window = scan[(scan["k"] >= lo) & (scan["k"] <= hi)]
    best_k = int(window.loc[window["silhouette"].idxmax(), "k"])
    log.info("Selected k=%d (best silhouette within business window %s)", best_k, K_BUSINESS_WINDOW)
    return best_k, scan


def plot_scan(scan: pd.DataFrame, best_k: int):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    a1.plot(scan["k"], scan["inertia"], "o-", color="#2C6E49")
    a1.set(title="Elbow (inertia)", xlabel="k", ylabel="inertia")
    a1.axvline(best_k, ls="--", color="grey")
    a2.plot(scan["k"], scan["silhouette"], "o-", color="#C4785B")
    a2.set(title="Silhouette score", xlabel="k", ylabel="silhouette")
    a2.axvline(best_k, ls="--", color="grey")
    fig.suptitle(f"Choosing k — selected k={best_k}", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG / "seg_elbow_silhouette.png", dpi=130)
    plt.close(fig)


def plot_pca(X: np.ndarray, labels: np.ndarray):
    pcs = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(X)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    sc = ax.scatter(pcs[:, 0], pcs[:, 1], c=labels, cmap="Set2", s=10, alpha=0.6)
    ax.set(title="Customer segments (PCA of RFMTC features)", xlabel="PC1", ylabel="PC2")
    legend = ax.legend(*sc.legend_elements(), title="cluster", loc="best")
    ax.add_artist(legend)
    fig.tight_layout()
    fig.savefig(FIG / "seg_pca_scatter.png", dpi=130)
    plt.close(fig)


def profile(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("cluster")
    prof = g.agg(
        members=("customer_id", "size"),
        recency_days=("recency_days", "mean"),
        frequency=("frequency", "mean"),
        monetary=("monetary", "mean"),
        tenure_days=("tenure_days", "mean"),
        churn_prob=("churn_prob", "mean"),
        total_monetary=("monetary", "sum"),
    ).round(2)
    prof["members_pct"] = (prof["members"] / prof["members"].sum() * 100).round(1)
    prof["revenue_pct"] = (prof["total_monetary"] / prof["total_monetary"].sum() * 100).round(1)
    # Profit-potential score: current value retained by likelihood of staying alive.
    prof["retainable_value"] = (prof["total_monetary"] * (1 - prof["churn_prob"])).round(0)
    prof = prof.sort_values("total_monetary", ascending=False)
    return prof


def name_segments(prof: pd.DataFrame) -> dict:
    """Scalable, unique descriptive labels from the RFMTC profile (works for any k)."""
    from collections import Counter
    q1, q2 = prof["monetary"].quantile([1/3, 2/3])
    rec_med = prof["recency_days"].median()
    chu_med = prof["churn_prob"].median()

    def base(r):
        val = "High-value" if r["monetary"] >= q2 else ("Mid-value" if r["monetary"] >= q1 else "Low-value")
        act = "active" if r["recency_days"] <= rec_med else "lapsing"
        risk = ", at-risk" if r["churn_prob"] >= chu_med else ""
        return f"{val}, {act}{risk}"

    raw = {c: base(r) for c, r in prof.iterrows()}
    counts = Counter(raw.values())
    seen = Counter()
    names = {}
    for c in prof.sort_values("monetary", ascending=False).index:
        lbl = raw[c]
        if counts[lbl] > 1:
            seen[lbl] += 1
            lbl = f"{lbl} #{seen[lbl]}"
        names[c] = lbl
    return names


def main():
    df, feat = assemble_rfmtc()
    scaler = StandardScaler()
    X = scaler.fit_transform(feat.values)

    best_k, scan = choose_k(X)
    plot_scan(scan, best_k)

    km = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10).fit(X)
    df["cluster"] = km.labels_
    plot_pca(X, km.labels_)

    prof = profile(df)
    labels = name_segments(prof)
    prof["segment"] = prof.index.map(labels)
    df["segment"] = df["cluster"].map(labels)

    # Top 3 by profit potential (retainable value)
    top3 = prof.sort_values("retainable_value", ascending=False).head(3)

    prof.to_csv(TAB / "segment_profile.csv")
    keep = ["customer_id", "cluster", "segment", "recency_days", "frequency",
            "monetary", "tenure_days", "churn_prob", "p_alive"]
    df[keep].to_parquet(PROC / "customer_segments.parquet", index=False)

    pd.set_option("display.width", 160, "display.max_columns", 20)
    print("\n=== SEGMENT PROFILE (sorted by total monetary) ===")
    print(prof[["segment", "members", "members_pct", "recency_days", "frequency",
                "monetary", "tenure_days", "churn_prob", "revenue_pct", "retainable_value"]].to_string())
    print("\n=== TOP 3 SEGMENTS BY PROFIT POTENTIAL (retainable value = value x P(alive)) ===")
    for c, r in top3.iterrows():
        print(f"  [{r['segment']}] members={int(r['members'])} ({r['members_pct']}%) | "
              f"avg spend={r['monetary']:.0f} | churn_prob={r['churn_prob']:.2f} | "
              f"revenue share={r['revenue_pct']}% | retainable value={r['retainable_value']:.0f}")
    print(f"\nk={best_k} | members={len(df)} | artifacts -> reports/figures, reports/tables, data/processed")


if __name__ == "__main__":
    main()
