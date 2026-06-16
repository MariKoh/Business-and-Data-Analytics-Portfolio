"""
Analysis 4 — Weekly demand forecasting (global XGBoost) + newsvendor stocking.

Objective (profit, not accuracy): forecast top-100 SKU weekly demand well enough to set
profit-optimal stock levels. 1-week-ahead. Honest framing: proxy is UK gift/homeware, so
the model learns UK seasonality (Christmas); Thai festival/payday features are the
documented production localisation (see scaling-to-production.md).

  * Panel reindexed to a full weekly grid (missing weeks = 0 demand).
  * Features: lags 1-4/8/52, rolling mean/std, calendar (weekofyear, month, December), sku.
  * Baseline: 4-week moving average. Model: global XGBoost regressor.
  * Metrics: WAPE (primary) + RMSE; MAPE skipped (zero-demand weeks).
  * Newsvendor: order qty = forecast + z*sigma, z = Phi^-1(critical ratio), CR from a
    margin + holding-cost assumption (durable goods -> overage is holding, not write-off).

Run:  python -m src.forecasting.forecast
"""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
TOP_N = 100
HOLDOUT_WEEKS = 12
MARGIN = 0.35          # assumed gross margin (no COGS in data)
HOLDING_FRAC = 0.25    # overage cost = 25% of unit cost (durable goods, not write-off)

def wape(y, yhat): return np.sum(np.abs(y - yhat)) / max(np.sum(y), 1e-9)
def rmse(y, yhat): return float(np.sqrt(np.mean((y - yhat) ** 2)))
def mae(y, yhat): return float(np.mean(np.abs(y - yhat)))            # real units
def bias(y, yhat): return float(np.mean(yhat - y))                   # +over / -under forecast

def main():
    sku = pd.read_parquet(PROC / "sku_timeseries.parquet")
    sku["week"] = pd.to_datetime(sku["week"])
    top = sku.groupby("stock_code")["revenue"].sum().sort_values(ascending=False).head(TOP_N).index
    s = sku[sku["stock_code"].isin(top)].copy()

    # full weekly grid per SKU (missing weeks -> 0 demand)
    weeks = pd.date_range(s["week"].min(), s["week"].max(), freq="W-MON")
    panel = (s.set_index(["stock_code", "week"])["quantity"]
               .unstack(fill_value=0).reindex(columns=weeks, fill_value=0)
               .stack().rename("quantity").reset_index())
    panel.columns = ["stock_code", "week", "quantity"]
    panel = panel.sort_values(["stock_code", "week"])

    g = panel.groupby("stock_code")["quantity"]
    for L in (1, 2, 3, 4, 8, 52):
        panel[f"lag{L}"] = g.shift(L)
    panel["roll4_mean"] = g.shift(1).rolling(4).mean().reset_index(0, drop=True)
    panel["roll8_mean"] = g.shift(1).rolling(8).mean().reset_index(0, drop=True)
    panel["roll4_std"] = g.shift(1).rolling(4).std().reset_index(0, drop=True)
    panel["woy"] = panel["week"].dt.isocalendar().week.astype(int)
    panel["month"] = panel["week"].dt.month
    panel["is_december"] = (panel["month"] == 12).astype(int)
    panel["sku_cat"] = panel["stock_code"].astype("category")

    data = panel.dropna(subset=["lag1", "lag2", "lag3", "lag4", "roll4_mean"]).copy()
    cutoff = weeks[-HOLDOUT_WEEKS]
    train, test = data[data["week"] < cutoff], data[data["week"] >= cutoff]

    feats = ["lag1", "lag2", "lag3", "lag4", "lag8", "lag52", "roll4_mean", "roll8_mean",
             "roll4_std", "woy", "month", "is_december", "sku_cat"]
    Xtr, ytr = train[feats], train["quantity"]
    Xte, yte = test[feats], test["quantity"]

    model = XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.04,
                         subsample=0.9, colsample_bytree=0.9, min_child_weight=5,
                         enable_categorical=True, tree_method="hist", random_state=42)
    model.fit(Xtr, np.log1p(ytr))                       # log target for spiky demand
    pred = np.clip(np.expm1(model.predict(Xte)), 0, None)

    base = test["roll4_mean"].values            # 4-week moving-average baseline
    seas = test["lag52"].fillna(test["roll4_mean"]).values  # seasonal-naive (last year)

    res = pd.DataFrame({"stock_code": test["stock_code"].values, "week": test["week"].values,
                        "actual": yte.values, "forecast": pred, "baseline_ma": base})
    metrics = {
        "WAPE_baseline_MA": wape(yte.values, base),
        "WAPE_seasonal_naive": wape(yte.values, seas),
        "WAPE_xgboost": wape(yte.values, pred),
        "MAE_baseline_MA_units": mae(yte.values, base),
        "MAE_xgboost_units": mae(yte.values, pred),
        "RMSE_baseline_MA_units": rmse(yte.values, base),
        "RMSE_xgboost_units": rmse(yte.values, pred),
        "Bias_xgboost_units": bias(yte.values, pred),
    }

    # --- per-SKU honest diagnostic (aggregate WAPE is volume-weighted) ---
    per = res.groupby("stock_code").apply(
        lambda d: pd.Series({"wape_xgb": wape(d["actual"].values, d["forecast"].values),
                             "wape_ma": wape(d["actual"].values, d["baseline_ma"].values),
                             "volume": d["actual"].sum()}), include_groups=False)
    xgb_win_rate = float((per["wape_xgb"] < per["wape_ma"]).mean())
    med_xgb, med_ma = float(per["wape_xgb"].median()), float(per["wape_ma"].median())

    # --- newsvendor stocking ---
    CR = MARGIN / (MARGIN + HOLDING_FRAC * (1 - MARGIN))   # critical ratio
    z = norm.ppf(CR)
    sigma = res.groupby("stock_code").apply(
        lambda d: np.std(d["actual"] - d["forecast"]), include_groups=False).rename("sigma")
    res = res.merge(sigma, on="stock_code")
    res["order_qty"] = np.clip(res["forecast"] + z * res["sigma"], 0, None).round()

    TAB.mkdir(parents=True, exist_ok=True)
    res.to_parquet(PROC / "forecast_holdout.parquet", index=False)
    pd.Series(metrics).round(3).to_csv(TAB / "forecast_metrics.csv")

    # --- figure: actual vs forecast for top-6 SKUs ---
    top6 = res.groupby("stock_code")["actual"].sum().sort_values(ascending=False).head(6).index
    # Label panels with the product NAME (not the SKU code) for readability.
    namemap = (pd.read_csv(PROC / "category_map.csv")
                 .assign(stock_code=lambda d: d["stock_code"].astype(str))
                 .drop_duplicates("stock_code").set_index("stock_code")["description"].to_dict())
    def _label(sc):
        nm = str(namemap.get(str(sc), sc)).strip().title()
        return nm if len(nm) <= 30 else nm[:29] + "."
    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    for ax, sc in zip(axes.ravel(), top6):
        d = res[res["stock_code"] == sc].sort_values("week")
        ax.plot(d["week"], d["actual"], "o-", color="#2C2C2C", lw=1.5, ms=3, label="actual")
        ax.plot(d["week"], d["forecast"], "s--", color="#2C6E49", lw=1.5, ms=3, label="forecast")
        ax.set_title(_label(sc), fontsize=9); ax.tick_params(labelsize=7)
    axes.ravel()[0].legend(fontsize=8)
    fig.suptitle("1-week-ahead demand forecast vs actual (top SKUs, 12-week holdout)", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "forecast_top_skus.png", dpi=135)

    print(f"=== DEMAND FORECAST (top {TOP_N} SKUs | {HOLDOUT_WEEKS}-week holdout | {len(weeks)} weeks) ===")
    for k, v in metrics.items():
        print(f"  {k:22s} {v:.3f}")
    lift = (metrics["WAPE_baseline_MA"] - metrics["WAPE_xgboost"]) / metrics["WAPE_baseline_MA"] * 100
    print(f"\nAggregate WAPE: XGBoost vs 4-week-MA baseline = {lift:+.1f}%")
    print(f"Per-SKU: XGB beats MA on {xgb_win_rate:.0%} of SKUs | median WAPE  XGB={med_xgb:.2f}  MA={med_ma:.2f}")
    print(f"Newsvendor: margin={MARGIN:.0%}, holding={HOLDING_FRAC:.0%} of cost "
          f"-> critical ratio={CR:.2f} (service level {CR:.0%}), z={z:.2f}")
    print(f"  -> order qty = forecast + {z:.2f} x sigma  (stock above forecast to protect availability)")
    print("saved -> forecast_top_skus.png, forecast_holdout.parquet, forecast_metrics.csv")

if __name__ == "__main__":
    main()
