"""Profiling helpers for the Phase-1 data-understanding step.

These produce the tables and the chart the cleaning notebook uses to answer two
questions before any cleaning: *which columns do we need?* and *which rows do we
need?* - and to document the missing-value situation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def overview(df: pd.DataFrame) -> pd.Series:
    """One-line shape/size summary of a raw or cleaned frame."""
    return pd.Series({
        "rows": len(df),
        "columns": df.shape[1],
        "memory_MB": round(df.memory_usage(deep=True).sum() / 1e6, 1),
        "duplicate_rows": int(df.duplicated().sum()),
    })


def column_profile(df: pd.DataFrame, n_examples: int = 3) -> pd.DataFrame:
    """Per-column dtype, missing count/%, distinct count, and example values."""
    rows = []
    for col in df.columns:
        s = df[col]
        examples = s.dropna().unique()[:n_examples]
        rows.append({
            "column": col,
            "dtype": str(s.dtype),
            "n_missing": int(s.isna().sum()),
            "pct_missing": round(100 * s.isna().mean(), 2),
            "n_unique": int(s.nunique(dropna=True)),
            "examples": ", ".join(map(str, examples)),
        })
    return pd.DataFrame(rows)


def missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Missing count and percentage per column, highest first."""
    out = pd.DataFrame({
        "n_missing": df.isna().sum(),
        "pct_missing": (100 * df.isna().mean()).round(2),
    })
    return out.sort_values("pct_missing", ascending=False)


def plot_missingness(df: pd.DataFrame, path: str | Path) -> Path:
    """Save a horizontal bar chart of % missing per column."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    miss = missingness(df)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 0.5 * len(miss) + 1))
    ax.barh(miss.index, miss["pct_missing"], color="#1f77b4")
    ax.invert_yaxis()
    ax.set_xlabel("% missing")
    ax.set_title("Missing values by column (raw data)")
    for y, v in enumerate(miss["pct_missing"]):
        ax.text(v + 0.2, y, f"{v:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def column_relevance() -> pd.DataFrame:
    """Documented keep/drop verdict per raw column - 'are these columns needed?'.

    All eight columns are retained; each maps to at least one analysis. The
    cleaning that follows removes *rows*, not columns.
    """
    rows = [
        ("Invoice",     "Keep", "Basket analysis, de-dup, cancellation flag",
         "Basket key. Leading 'C' marks a cancellation -> dropped."),
        ("StockCode",   "Keep", "Forecasting, basket, product master",
         "Product key. Non-SKU service codes (POST, DOT, ...) flagged, not sold."),
        ("Description", "Keep", "Human-readable product label, product master",
         "Has some missing values; filled from the modal description per SKU."),
        ("Quantity",    "Keep", "Revenue, demand forecasting, inventory",
         "Non-positive values (returns/adjustments) dropped."),
        ("InvoiceDate", "Keep", "Forecasting, recency, seasonality, date dim",
         "Parsed to datetime; spans 2009-12 to 2011-12."),
        ("Price",       "Keep", "Revenue, gross-margin model",
         "Unit price (GBP). Non-positive values dropped."),
        ("Customer ID", "Keep", "Segmentation, CLV, churn (member-level)",
         "Missing for guest baskets; required only for member-level analysis."),
        ("Country",     "Keep", "Geography, segmentation, country dim",
         "Low cardinality; UK dominates."),
    ]
    return pd.DataFrame(rows, columns=["column", "verdict", "used_for", "note"])
