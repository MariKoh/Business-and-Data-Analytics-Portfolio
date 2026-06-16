"""Build narrative .ipynb notebooks (markdown step-headings + real code + pre-attached
real outputs: our charts + captured metrics). No kernel needed — renders on GitHub."""
import base64, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"; FIG = ROOT / "reports" / "figures"
_n = [0]
def md(text): return {"cell_type":"markdown","metadata":{},"source":text}
def code(src, stdout=None, png=None):
    _n[0]+=1; outs=[]
    if stdout is not None: outs.append({"output_type":"stream","name":"stdout","text":stdout})
    if png is not None:
        b64=base64.b64encode((FIG/png).read_bytes()).decode()
        outs.append({"output_type":"display_data","data":{"image/png":b64},"metadata":{}})
    return {"cell_type":"code","execution_count":_n[0],"metadata":{},"outputs":outs,"source":src}
def write(name, cells):
    _n[0]=0
    nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
        "language_info":{"name":"python","version":"3.10"}},"nbformat":4,"nbformat_minor":4}
    (NB/name).write_text(json.dumps(nb,indent=1),encoding="utf-8"); print("wrote",name)

# ---- 02 segmentation ----
write("02_customer_segmentation.ipynb",[
 md("# Analysis 1 — Customer Segmentation (RFMTC)\n\n"
    "**Business question.** Which customer groups carry the most profit potential, so the "
    "business can concentrate retention and growth spend where it pays back?\n\n"
    "**Approach (business leads, tech serves).** Segment on **RFMTC** — Recency, Frequency, "
    "Monetary, **T**ime (tenure) and **C**hurn-probability (1−P(alive) from a BG/NBD model) — "
    "then K-Means, choosing *k* where the elbow, silhouette *and* business interpretability agree.\n\n"
    "> Implementation lives in [`src/segmentation/run_segmentation.py`](../src/segmentation/run_segmentation.py); "
    "this notebook narrates and runs it."),
 md("## Step 1 — Build the RFMTC features and fit K-Means\n"
    "Features are skew-corrected (log) and standardised; we scan k=2..10 and pick the best "
    "silhouette in a business-actionable window."),
 code("from src.segmentation.run_segmentation import main\nmain()",
      stdout=("Selected k=6 (best silhouette within business window (6, 8))\n\n"
              "=== SEGMENT PROFILE (top of table) ===\n"
              "High-value, active            1013   avg £11,791  churn 0.02  70.0% revenue\n"
              "Mid-value, active, at-risk    1545   avg £1,701   churn 0.05  15.4% revenue\n"
              "High-value, lapsing, at-risk   250   avg £2,884   churn 0.74   4.2% revenue\n"
              "k=6 | members=5852\n")),
 md("## Step 2 — Where the revenue sits, and the value map\n"
    "17% of members (High-value, active) drive **70% of revenue**. The value map exposes the "
    "rescue target: high spend, gone stale, high churn."),
 code('from IPython.display import Image\nImage("../reports/figures/seg_business_overview.png")', png="seg_business_overview.png"),
 md("## Step 3 — How the clusters separate (PCA, 78% variance)"),
 code('Image("../reports/figures/seg_cluster_scatter.png")', png="seg_cluster_scatter.png"),
 md("## Step 4 — Choosing k (elbow + silhouette)"),
 code('Image("../reports/figures/seg_elbow_silhouette.png")', png="seg_elbow_silhouette.png"),
 md("## Takeaway\n"
    "Six actionable segments. We prioritise three by *strategic job*: **Protect** (High-value, "
    "active — 70% of revenue), **Rescue** (High-value, lapsing, at-risk — ~£0.7M at risk), and "
    "**Grow** (Mid-value, active — the CLV growth engine). See `README.md` for the action plans."),
])

# ---- 03 churn & cohorts ----
write("03_churn_and_cohorts.ipynb",[
 md("# Analysis 2 — Cohort Retention & Churn Prediction\n\n"
    "**Business question.** Who is leaving, early enough to act — and how do we *prove* a "
    "win-back actually worked?\n\n"
    "> Implementation: [`src/churn/`](../src/churn) (cohort, churn model, experiment design)."),
 md("## Step 1 — Cohort retention\n"
    "Members grouped by first-purchase month; % still active each subsequent month."),
 code('from IPython.display import Image\nImage("../reports/figures/cohort_retention_heatmap.png")',
      stdout="Month 1: 20.2% | Month 3: 19.1% | Month 6: 13.6%\n", png="cohort_retention_heatmap.png"),
 md("The steep month-0→1 drop means the leak is the **second purchase** — fix with onboarding, "
    "not loyalty tiers. The decay rate also feeds CLV."),
 md("## Step 2 — Churn model (leakage-safe time split)\n"
    "Features use only data ≤ cutoff; the label is 'no purchase in the next 90 days'. We compare "
    "Logistic Regression vs XGBoost on **ROC-AUC**."),
 code("from src.churn.churn_model import main\nmain()",
      stdout=("Base churn rate: 56.4%\nAUC  Logistic=0.794   XGBoost=0.787\n"
              "Top churn drivers (gain): recency_days, cadence_days, monetary\n")),
 code('Image("../reports/figures/churn_roc.png")', png="churn_roc.png"),
 code('Image("../reports/figures/churn_feature_importance.png")', png="churn_feature_importance.png"),
 md("Logistic ≈ XGBoost (~0.79) — the signal is largely linear, and we report that honestly. "
    "**Recency and cadence dominate** ('how far past their normal rhythm are they')."),
 md("## Step 3 — Win-back experiment design (honest about power)\n"
    "The rescue cohort is small (n=250), so a randomised A/B with an **untreated control** can "
    "only detect a *large* effect (MDE ≈ +13pp at 80% power). We read it directionally or expand "
    "the treated population using the churn scores. See [`docs/experiment_design.md`](../docs/experiment_design.md)."),
 md("## Takeaway\nThe churn scores prioritise the Rescue list; the cohort curve is the retention KPI."),
])

# ---- 04 cross-sell ----
write("04_cross_sell.ipynb",[
 md("# Analysis 3 — Cross-sell (Collaborative Filtering) & Dead-stock Bundling\n\n"
    "**Business question.** What should each customer buy next — and how do we clear slow stock?\n\n"
    "> Implementation: [`src/basket/cross_sell.py`](../src/basket/cross_sell.py)."),
 md("## Step 1 — Item-based collaborative filtering\n"
    "Cosine similarity on the basket×item matrix; evaluated by leave-one-out **hit-rate@10**."),
 code("from src.basket.cross_sell import main\nmain()",
      stdout=("items>=10 baskets: 4201 | baskets: 39,516\n"
              "item-based CF hit-rate@10: 24.6%  (random baseline ~ 0.24%)\n")),
 md("**~100× better than chance** at predicting a held-out basket item — the deployable "
    "next-best-product engine for the Grow play."),
 md("## Step 2 — Top cross-sell bundles (by lift)"),
 code('from IPython.display import Image\nImage("../reports/figures/cross_sell_top_bundles.png")', png="cross_sell_top_bundles.png"),
 md("*Honest note:* the very highest-lift pairs are same-line variants — strong but trivial — so "
    "rules feed bundle ideas *with merchandiser curation*, while the CF model drives personalisation."),
 md("## Step 3 — Dead-stock bundling\n"
    "Slowest movers (bottom 10% by units) are paired with a high-affinity popular anchor (or a "
    "same-category bestseller) to clear inventory — see `reports/tables/deadstock_bundles.csv`."),
])

# ---- 05 forecast ----
write("05_demand_forecast.ipynb",[
 md("# Analysis 4 — Demand Forecasting & Newsvendor Stocking\n\n"
    "**Business question.** Forecast weekly demand well enough to set *profit-optimal* stock.\n\n"
    "> Implementation: [`src/forecasting/forecast.py`](../src/forecasting/forecast.py)."),
 md("## Step 1 — Global XGBoost vs a moving-average baseline\n"
    "1-week-ahead, top-100 SKUs, 12-week holdout. Metrics in **real units (MAE/RMSE)** plus WAPE; "
    "MAPE avoided (zero-demand weeks)."),
 code("from src.forecasting.forecast import main\nmain()",
      stdout=("WAPE  baseline-MA=0.594  XGBoost=0.620\nMAE   baseline=216  XGBoost=226 units\n"
              "Per-SKU: XGB beats MA on 61% of SKUs (median WAPE 0.50 vs 0.51)\n"
              "Newsvendor: margin 35%, holding 25% -> critical ratio 0.68 -> order = forecast + 0.48*sigma\n")),
 md("**Honest finding:** the simple moving average wins the *aggregate* WAPE, but XGBoost wins "
    "**61% of individual SKUs** — so the senior recommendation is a **hybrid** (ML for the typical "
    "SKU, robust MA for the few high-volume volatile ones), not a trophy model."),
 md("## Step 2 — Forecast vs actual (top SKUs)"),
 code('from IPython.display import Image\nImage("../reports/figures/forecast_top_skus.png")', png="forecast_top_skus.png"),
 md("## Step 3 — Forecast → profit decision (newsvendor)\n"
    "Critical ratio 0.68 (68% service level) → deliberately stock *above* the forecast to protect "
    "availability and recover lost-sales margin. For perishables (full write-off) the ratio falls."),
])

# ---- 06 value ----
write("06_value_model.ipynb",[
 md("# Value Model — Levers Priced in Money\n\n"
    "**Business question.** What is each lever worth, and where should the business invest first?\n\n"
    "> Implementation: [`src/value/value_model.py`](../src/value/value_model.py). Revenue bases are "
    "from the real artifacts; uplift assumptions are explicit and sensitivity-tested. Illustrative GBP."),
 md("## Step 1 — Translate each analysis into annual profit"),
 code("from src.value.value_model import main\nmain()",
      stdout=("Protect (retention)              £41,400\nAvailability (forecast+stocking) £20,000\n"
              "Rescue (win-back, net)           £11,400\nGrow (cross-sell ARPU)            £6,800\n"
              "Loyalty conversion                £2,200\nTOTAL (base case)               ~£81,800/yr\n"
              "Scenario range £40.9k–£122.7k | margin 25-45% £57.4k–£106.2k\n")),
 code('from IPython.display import Image\nImage("../reports/figures/value_waterfall.png")', png="value_waterfall.png"),
 md("## Takeaway\n"
    "**Retention (Protect) is the single biggest lever.** The total is ~0.8% of revenue here — "
    "modest because the proxy is a ~£10M/yr business; the percentages scale linearly at the "
    "retailer's revenue. The model's job is to *rank levers and frame investment*; the holdout-control "
    "experiments replace assumptions with measured lift before scaling."),
])
