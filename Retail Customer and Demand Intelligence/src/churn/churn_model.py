"""
Analysis 2b — Churn prediction (non-contractual, leakage-safe time split).

Design:
  * cutoff = max_date - HORIZON. Features use ONLY data <= cutoff; the label uses the
    outcome window (cutoff, max_date]. churn = 1 if the member made NO purchase in the
    outcome window. This strict time split prevents leakage.
  * Members only (customer-level model).
  * Models: Logistic Regression (baseline) + XGBoost. Primary metric: ROC-AUC.
  * Outputs ROC curve, feature importance, and per-member churn scores (for Rescue).

Run:  python -m src.churn.churn_model
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
HORIZON_DAYS = 90
FEATURES = ["recency_days", "frequency", "monetary", "tenure_days",
            "avg_basket_value", "avg_items", "distinct_skus", "cadence_days", "overdue_ratio"]

def build_dataset():
    tx = pd.read_parquet(PROC / "model_transactions.parquet")
    tx = tx[tx["member_status"] == "Member"].copy()
    tx["customer_id"] = tx["customer_id"].astype("int64")
    max_date = tx["invoice_date"].max()
    cutoff = max_date - pd.Timedelta(days=HORIZON_DAYS)

    fw = tx[tx["invoice_date"] <= cutoff]
    ow_customers = set(tx[tx["invoice_date"] > cutoff]["customer_id"].unique())

    g = fw.groupby("customer_id")
    d = g.agg(last=("invoice_date", "max"), first=("invoice_date", "min"),
              frequency=("invoice", "nunique"), monetary=("revenue", "sum"),
              total_qty=("quantity", "sum"), distinct_skus=("stock_code", "nunique"))
    d["recency_days"] = (cutoff - d["last"]).dt.days
    d["tenure_days"] = (cutoff - d["first"]).dt.days
    d["avg_basket_value"] = d["monetary"] / d["frequency"]
    d["avg_items"] = d["total_qty"] / d["frequency"]
    d["cadence_days"] = np.where(d["frequency"] > 1, d["tenure_days"] / (d["frequency"] - 1),
                                 d["tenure_days"].clip(lower=1))
    d["overdue_ratio"] = d["recency_days"] / d["cadence_days"].clip(lower=1)
    d["churn"] = (~d.index.isin(ow_customers)).astype(int)
    return d.reset_index(), cutoff, max_date

def main():
    d, cutoff, max_date = build_dataset()
    X, y = d[FEATURES], d["churn"]
    base = y.mean()

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)

    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
    lr.fit(Xtr, ytr); p_lr = lr.predict_proba(Xte)[:, 1]; auc_lr = roc_auc_score(yte, p_lr)

    xgb = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                        subsample=0.9, colsample_bytree=0.9, eval_metric="auc",
                        importance_type="gain", random_state=42)
    xgb.fit(Xtr, ytr); p_xgb = xgb.predict_proba(Xte)[:, 1]; auc_xgb = roc_auc_score(yte, p_xgb)

    # ROC plot
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for name, p, auc, c in [("Logistic Reg", p_lr, auc_lr, "#C4785B"), ("XGBoost", p_xgb, auc_xgb, "#2C6E49")]:
        fpr, tpr, _ = roc_curve(yte, p)
        ax.plot(fpr, tpr, color=c, lw=2, label=f"{name} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)
    ax.set(xlabel="False positive rate", ylabel="True positive rate",
           title=f"Churn model ROC (90-day horizon)\nbase churn rate = {base:.1%}")
    ax.legend(loc="lower right"); fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / "churn_roc.png", dpi=140)

    # feature importance (XGB gain)
    imp = pd.Series(xgb.feature_importances_, index=FEATURES).sort_values()
    fig2, ax2 = plt.subplots(figsize=(7.5, 5))
    ax2.barh(imp.index, imp.values, color="#2C6E49")
    ax2.set_title("Churn drivers — XGBoost feature importance (gain)", fontweight="bold")
    fig2.tight_layout(); fig2.savefig(FIG / "churn_feature_importance.png", dpi=140)

    # score all members with the stronger model (fit on full data)
    xgb_full = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                             subsample=0.9, colsample_bytree=0.9, eval_metric="auc",
                             importance_type="gain", random_state=42).fit(X, y)
    d["churn_prob_pred"] = xgb_full.predict_proba(X)[:, 1]
    TAB.mkdir(parents=True, exist_ok=True)
    d[["customer_id", "churn", "churn_prob_pred"] + FEATURES].to_parquet(PROC / "churn_scores.parquet", index=False)

    yhat = (p_xgb >= 0.5).astype(int)
    print(f"=== CHURN MODEL (cutoff {cutoff.date()} | horizon {HORIZON_DAYS}d | {len(d):,} members) ===")
    print(f"Base churn rate: {base:.1%}")
    print(f"AUC  Logistic={auc_lr:.3f}   XGBoost={auc_xgb:.3f}")
    print("\nConfusion matrix (XGB @0.5):\n", confusion_matrix(yte, yhat))
    print("\n", classification_report(yte, yhat, digits=3))
    print("Top churn drivers (gain):")
    for f, v in imp.sort_values(ascending=False).head(5).items():
        print(f"   {f:18s} {v:.3f}")
    print("\nsaved -> churn_roc.png, churn_feature_importance.png, data/processed/churn_scores.parquet")

if __name__ == "__main__":
    main()
