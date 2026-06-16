"""
Cluster visualization (Analysis 1): 2D PCA of the RFMTC feature space, points
coloured by named segment, with labeled centroids. Reuses the saved cluster labels
in customer_segments.parquet (no re-clustering) and the same feature transform.
Run:  python -m src.segmentation.plot_clusters
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"

def main():
    df = pd.read_parquet(PROC / "customer_segments.parquet")
    feat = pd.DataFrame({
        "R": df["recency_days"],
        "F": np.log1p(df["frequency"]),
        "M": np.log1p(df["monetary"].clip(lower=0)),
        "T": df["tenure_days"],
        "C": df["churn_prob"],
    })
    X = StandardScaler().fit_transform(feat.values)
    pca = PCA(n_components=2, random_state=42)
    pcs = pca.fit_transform(X)
    ev = pca.explained_variance_ratio_ * 100
    df["pc1"], df["pc2"] = pcs[:, 0], pcs[:, 1]

    # order segments by avg spend (richest first) for a sensible colour/legend order
    order = (df.groupby("segment")["monetary"].mean().sort_values(ascending=False).index.tolist())
    cmap = plt.cm.tab10(np.linspace(0, 1, len(order)))

    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    for color, seg in zip(cmap, order):
        m = df["segment"] == seg
        ax.scatter(df.loc[m, "pc1"], df.loc[m, "pc2"], s=12, alpha=0.45,
                   color=color, label=f"{seg}  (n={int(m.sum()):,})")
        cx, cy = df.loc[m, "pc1"].mean(), df.loc[m, "pc2"].mean()
        ax.scatter(cx, cy, marker="X", s=240, color=color, edgecolor="#2C2C2C", linewidth=1.6, zorder=5)

    ax.set_xlabel(f"PC1 — {ev[0]:.0f}% of variance")
    ax.set_ylabel(f"PC2 — {ev[1]:.0f}% of variance")
    ax.set_title("Customer clusters in RFMTC space (PCA, k=6)\nX = segment centroid", fontweight="bold")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8, frameon=False)
    fig.tight_layout()
    out = FIG / "seg_cluster_scatter.png"
    fig.savefig(out, dpi=140)
    print(f"PC1+PC2 explain {ev[0]+ev[1]:.0f}% of variance | saved -> {out.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
