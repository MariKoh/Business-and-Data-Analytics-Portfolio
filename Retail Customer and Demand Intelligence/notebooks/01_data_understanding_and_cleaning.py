# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 01 · Data Understanding & Cleaning
#
# **Retail Customer-Intelligence Platform — Phase 1**
#
# This notebook makes the data-cleaning process *visible*. Working from the raw
# **UCI Online Retail II** workbook (a public proxy for the Retailer transaction data),
# we answer two questions before touching a model:
#
# 1. **Which columns do we need?**
# 2. **Which rows do we need?** (and how do we treat missing / invalid values)
#
# Business mapping: `StockCode → product/SKU`, `Invoice → basket`,
# `Customer ID → Clubcard member`.
#
# Every step below calls the shared functions in `src/data/clean.py`, so this
# narrated process is *identical* to the production cleaning used downstream.

# %%
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Make the repo root importable whether this runs from notebooks/ or the root.
ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
FIG_DIR = ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

from src.data import profiling  # noqa: E402
from src.data.clean import CLEANING_STEPS, clean_transactions, load_raw  # noqa: E402

# Keep step INFO logs quiet here — we narrate with explicit tables instead.
logging.getLogger("src.data.clean").setLevel(logging.WARNING)
sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", None)

# %% [markdown]
# ## 1. Load the raw data
#
# The workbook has two sheets (`Year 2009-2010`, `Year 2010-2011`) with identical
# columns; we concatenate them and rename to snake_case on load
# (`Invoice → invoice`, `StockCode → stock_code`, `Customer ID → customer_id`, …).

# %%
raw = load_raw()
print(f"Raw shape: {raw.shape[0]:,} rows × {raw.shape[1]} columns")
raw.head()

# %%
profiling.overview(raw)

# %% [markdown]
# ## 2. Which columns do we need?
#
# A per-column profile (dtype, missingness, distinct values, examples), then a
# documented keep/drop verdict. **Conclusion: all eight columns are useful** —
# each maps to at least one analysis — so cleaning removes *rows*, not columns.

# %%
profiling.column_profile(raw)

# %%
profiling.column_relevance()

# %% [markdown]
# ## 3. Missing values
#
# `customer_id` is missing on ~23% of lines — these are **guest / unidentified
# baskets**, not an error. We keep them for sales/forecasting/basket analysis and
# require an id only for member-level work (segmentation, CLV, churn).
# `description` has a tiny amount missing, later filled from the modal description
# per SKU.

# %%
profiling.missingness(raw)

# %%
miss = profiling.missingness(raw)
fig, ax = plt.subplots(figsize=(7, 3.5))
sns.barplot(x=miss["pct_missing"], y=miss.index, color="#1f77b4", ax=ax)
ax.set(xlabel="% missing", ylabel="", title="Missing values by column (raw data)")
for y, v in enumerate(miss["pct_missing"]):
    ax.text(v + 0.2, y, f"{v:.1f}%", va="center", fontsize=9)
fig.tight_layout()
fig.savefig(FIG_DIR / "01_missingness.png", dpi=120)
plt.show()

# %% [markdown]
# ## 4. Which rows do we need? — cleaning, step by step
#
# We apply each cleaning step in order and audit how many rows it removes. The
# steps: standardise dtypes → drop unparseable dates → drop exact duplicates →
# drop cancellations (`C`-invoices) → drop non-positive qty/price → flag product
# vs service codes → add line revenue. (The dtype/flag/revenue steps transform or
# add columns and remove zero rows — shown explicitly for transparency.)

# %%
df = raw.copy()
audit = []
for label, step in CLEANING_STEPS:
    before = len(df)
    df = step(df)
    audit.append({
        "step": label,
        "rows_before": before,
        "rows_after": len(df),
        "rows_removed": before - len(df),
        "pct_removed": round(100 * (before - len(df)) / before, 2),
    })
audit_df = pd.DataFrame(audit)
audit_df

# %% [markdown]
# The cleaned frame produced by these steps is exactly `clean_transactions(raw)`:

# %%
clean = df.reset_index(drop=True)
assert len(clean) == len(clean_transactions(raw)), "narrated steps must match production"
print(f"Clean shape: {clean.shape[0]:,} rows × {clean.shape[1]} columns")
print(f"Retained {100 * len(clean) / len(raw):.1f}% of raw rows")

# %% [markdown]
# ## 5. The cleaned dataset — before vs after

# %%
pd.concat([profiling.overview(raw).rename("raw"),
           profiling.overview(clean).rename("clean")], axis=1)

# %%
# Cleaning impact: rows removed at each step, then what remains.
removed = audit_df[audit_df["rows_removed"] > 0]
labels = list(removed["step"]) + ["retained (clean)"]
values = list(removed["rows_removed"]) + [len(clean)]
colors = ["#d62728"] * len(removed) + ["#2ca02c"]

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(labels, values, color=colors)
ax.set(ylabel="rows", title="Cleaning impact (rows removed per step vs retained)")
ax.tick_params(axis="x", rotation=30)
for i, v in enumerate(values):
    ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
plt.setp(ax.get_xticklabels(), ha="right")
fig.tight_layout()
fig.savefig(FIG_DIR / "01_cleaning_impact.png", dpi=120)
plt.show()

# %%
# Product vs service lines in the clean data, and headline counts.
print("Product vs service lines:")
print(clean["is_product"].value_counts().rename({True: "product", False: "service/admin"}))
print(f"\nDate range : {clean['invoice_date'].min().date()} → {clean['invoice_date'].max().date()}")
print(f"Members    : {clean['customer_id'].nunique():,} (rows with an id)")
print(f"Products   : {clean.loc[clean['is_product'], 'stock_code'].nunique():,}")
print(f"Baskets    : {clean['invoice'].nunique():,}")
clean.head()

# %% [markdown]
# ## 6. Output & productionization
#
# This exact pipeline lives in `src/data/clean.py` (`clean_transactions`). Running
#
# ```bash
# python -m src.pipeline.build_features
# ```
#
# writes the cleaned line-level table to `data/processed/clean_transactions.parquet`
# (the input for Phase 2's star-schema warehouse) plus the three feature marts.
#
# **Cleaning decisions (summary):** drop exact duplicates; drop cancellations
# (`C`-invoices are returns); drop non-positive quantity/price (adjustments,
# freebies); flag non-SKU service codes (POST, DOT, fees) so they don't pollute
# product analytics; keep guest baskets (null `customer_id`) for everything except
# member-level work. Full column reference: `docs/data_dictionary.md`;
# narrative: `docs/cleaning_report.md`.
