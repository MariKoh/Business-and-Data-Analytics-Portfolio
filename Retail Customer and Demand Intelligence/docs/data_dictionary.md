# Data Dictionary

All tables are produced by `src/pipeline/build_features.py` from the raw
**UCI Online Retail II** workbook and written to `data/processed/` as Parquet.

> **Public-proxy note.** Online Retail II is a real UK online-retail dataset used
> here as a stand-in for the retailer's omnichannel transaction data. The business
> framing below is how the same pipeline would map onto the retailer's systems; no
> the retailer's data is used.

## Business mapping

| Dataset field | the retailer's concept |
|---|---|
| `StockCode` | Product / SKU |
| `Invoice` | Shopping basket (one checkout) |
| `Customer ID` | Clubcard member |
| `Quantity` × `Price` | Line revenue |

---

## Raw source: `online_retail_II.xlsx`

Two sheets (`Year 2009-2010`, `Year 2010-2011`) with identical columns,
concatenated on load.

| Column | Type | Description |
|---|---|---|
| `Invoice` | str/int | Invoice number. A leading **`C`** marks a cancellation/return. |
| `StockCode` | str | Product code. Genuine SKUs are 5 digits, optionally with trailing letters (e.g. `85123A`). Other values are service/admin lines (postage `POST`/`DOT`, `BANK CHARGES`, `AMAZONFEE`, discounts `D`, manual `M`, `ADJUST`, gift vouchers, …). |
| `Description` | str | Product name. Occasionally missing. |
| `Quantity` | int | Units on the line. Negative on cancellations/adjustments. |
| `InvoiceDate` | datetime | Timestamp of the transaction. |
| `Price` | float | Unit price (GBP). |
| `Customer ID` | float | Clubcard member id. **Missing** for guest / unidentified baskets (~20% of lines). |
| `Country` | str | Customer's country. |

### Cleaning rules (applied in `clean_transactions`)

1. Columns renamed to `snake_case`; dates parsed; `customer_id` cast to nullable `Int64`.
2. **Exact duplicate rows dropped.**
3. **Cancellations dropped** (invoice starting with `C`).
4. **Non-positive `quantity` or `price` dropped** (returns, adjustments, freebies).
5. Each line flagged `is_product` via the SKU regex `^\d{5}[A-Za-z]*$`; service/admin
   lines are excluded from the SKU and basket tables (but counted in logs).
6. Line-level `revenue = quantity * price` added.

A small `dataset_summary.json` (row counts, date range, totals) is also written
to `data/processed/` for the README and the GenAI assistant.

---

## 1. `customer_features.parquet`

One row per Clubcard member (lines with a known `customer_id` only). Recency and
tenure are measured against a **snapshot date = last transaction date + 1 day**.

| Column | Type | Description |
|---|---|---|
| `customer_id` | Int64 | Clubcard member id (key). |
| `recency_days` | int | Days from the member's last purchase to the snapshot. **Lower = more recently active.** |
| `frequency` | int | Number of distinct baskets (invoices). |
| `monetary` | float | Total revenue from the member (GBP). |
| `total_quantity` | int | Total units purchased across all baskets. |
| `num_distinct_skus` | int | Number of distinct products ever bought. |
| `tenure_days` | int | Days from first purchase to snapshot (relationship age). |
| `avg_basket_value` | float | `monetary / frequency`. |
| `avg_items_per_basket` | float | `total_quantity / frequency`. |
| `first_purchase` | datetime | Date of first purchase. |
| `last_purchase` | datetime | Date of most recent purchase. |

*Used by:* Session 2 (RFM segmentation, CLV, churn).

---

## 2. `sku_timeseries.parquet`

Weekly sales per product. One row per (`stock_code`, `week`) for **active weeks**
(weeks with at least one sale). Product lines only.

| Column | Type | Description |
|---|---|---|
| `stock_code` | str | Product code (key). |
| `description` | str | Most frequent description seen for that product. |
| `week` | datetime | **Monday** of the sales week. |
| `quantity` | int | Units sold that week. |
| `revenue` | float | Revenue that week (GBP). |

> Weeks with no sales are intentionally omitted to keep the table compact across
> the full catalogue. The forecasting module reindexes its selected top-N SKUs
> onto a regular, gap-filled weekly grid (zeros for no-sale weeks).

*Used by:* Session 1 (demand forecasting).

---

## 3. `basket_transactions.parquet`

One row per basket (invoice). Product lines only, so association-rule mining is
not polluted by postage/admin codes.

| Column | Type | Description |
|---|---|---|
| `invoice` | str | Invoice number (key). |
| `invoice_date` | datetime | Basket timestamp (earliest line). |
| `customer_id` | Int64 | Clubcard member id, or null for a guest basket. |
| `country` | str | Customer country. |
| `n_lines` | int | Number of line items in the basket. |
| `n_distinct_items` | int | Number of distinct products in the basket. |
| `basket_revenue` | float | Total basket revenue (GBP). |
| `items` | list[str] | Sorted list of distinct StockCodes in the basket (input to mlxtend's TransactionEncoder). |

*Used by:* Session 3 (market basket / association rules).
