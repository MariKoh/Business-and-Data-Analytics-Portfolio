"""Composable cleaning steps for the UCI Online Retail II workbook.

Each step is a small, documented ``DataFrame -> DataFrame`` function that logs how
many rows it removes. The Phase-1 notebook calls them **one at a time** to narrate
the cleaning process with before/after counts, while production builds (warehouse,
feature marts) call the same functions through :func:`clean_transactions` - so the
narrated process and the productionized code are guaranteed identical.

Business framing: ``StockCode -> product/SKU``, ``Invoice -> basket``,
``Customer ID -> Clubcard member``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"

# Original -> snake_case column names.
COLUMN_RENAME = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}

# A genuine product code is 5 digits, optionally followed by letters (e.g.
# "85123A"). Everything else - POST, DOT, D, M, C2, BANK CHARGES, AMAZONFEE,
# ADJUST, gift vouchers, TEST... - is a service/admin line, not a sellable SKU.
PRODUCT_CODE_PATTERN = r"^\d{5}[A-Za-z]*$"

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def load_raw(path: Path = RAW_FILE) -> pd.DataFrame:
    """Read both workbook sheets, concatenate, and rename columns to snake_case."""
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}.\n"
            "Download UCI 'Online Retail II' (online_retail_II.xlsx) into data/raw/. "
            "See the README 'How to run' section."
        )
    log.info("Reading workbook %s (this can take ~1 minute) ...", path.name)
    sheets = pd.read_excel(path, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True).rename(columns=COLUMN_RENAME)
    log.info("Loaded %s raw rows from %d sheets: %s",
             f"{len(df):,}", len(sheets), list(sheets.keys()))
    return df


# --------------------------------------------------------------------------- #
# Cleaning steps (each logs the rows it removes)
# --------------------------------------------------------------------------- #
def standardise_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Trim text columns, parse ``invoice_date``, cast ``customer_id`` to Int64."""
    df = df.copy()
    df["invoice"] = df["invoice"].astype(str).str.strip()
    df["stock_code"] = df["stock_code"].astype(str).str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["customer_id"] = df["customer_id"].astype("Int64")
    return df


def drop_unparseable_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows whose invoice date could not be parsed (expected ~0)."""
    n = int(df["invoice_date"].isna().sum())
    if n:
        log.info("Dropped %s rows with unparseable invoice dates.", f"{n:,}")
    return df[df["invoice_date"].notna()]


def drop_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows (a known artefact of this dataset)."""
    before = len(df)
    out = df.drop_duplicates()
    log.info("Dropped %s exact duplicate rows.", f"{before - len(out):,}")
    return out


def drop_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    """Drop cancellation/return lines (invoice numbers prefixed with 'C')."""
    is_cancel = df["invoice"].str.upper().str.startswith("C")
    log.info("Dropped %s cancellation lines (invoice starts with 'C').",
             f"{int(is_cancel.sum()):,}")
    return df[~is_cancel]


def drop_nonpositive(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with non-positive quantity or price (adjustments, freebies)."""
    before = len(df)
    out = df[(df["quantity"] > 0) & (df["price"] > 0)]
    log.info("Dropped %s rows with non-positive quantity or price.",
             f"{before - len(out):,}")
    return out


def flag_product_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_product``: True for genuine SKUs, False for service/admin codes."""
    df = df.copy()
    df["is_product"] = df["stock_code"].str.match(PRODUCT_CODE_PATTERN)
    log.info("Flagged %s service/admin lines; %s product lines.",
             f"{int((~df['is_product']).sum()):,}", f"{int(df['is_product'].sum()):,}")
    return df


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Add line-level ``revenue = quantity * price``."""
    df = df.copy()
    df["revenue"] = df["quantity"] * df["price"]
    return df


# Ordered cleaning pipeline: (label, function). Used by clean_transactions and
# can be iterated by the notebook to build a before/after audit table.
CLEANING_STEPS = [
    ("standardise dtypes", standardise_dtypes),
    ("drop unparseable dates", drop_unparseable_dates),
    ("drop duplicate rows", drop_duplicate_rows),
    ("drop cancellations", drop_cancellations),
    ("drop non-positive qty/price", drop_nonpositive),
    ("flag product vs service codes", flag_product_codes),
    ("add line revenue", add_revenue),
]


def clean_transactions(df: pd.DataFrame, *, verbose: bool = True) -> pd.DataFrame:
    """Run the full cleaning pipeline (all steps in order) and return clean lines."""
    n0 = len(df)
    for _, step in CLEANING_STEPS:
        df = step(df)
    if verbose:
        log.info("Cleaning complete: %s -> %s rows (%.1f%% retained).",
                 f"{n0:,}", f"{len(df):,}", 100 * len(df) / n0)
    return df.reset_index(drop=True)
