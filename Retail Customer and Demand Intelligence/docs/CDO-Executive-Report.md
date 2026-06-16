# Retail Customer-Intelligence — Executive Report
### Office of the Chief Data Officer · Customer & Demand Intelligence

---

## 1. Executive summary

We turned two years of raw transaction data into a **profit engine** organised around one
goal: **grow gross-margin profit**, not just report numbers. Every model exists to move
that goal, and every recommendation is expressed in money and paired with an experiment
to prove it.

The headline: a disciplined, data-led operating model on this business is worth an
estimated **£82k/year in incremental profit at the base case** (range £41k–£123k) — **+2.4% of profit** on this small dataset, scaling to **~£8M/year at £1B revenue**, with an even larger *addressable* prize (~£0.7M actively at-risk + £2.57M of untracked guest revenue). And
the single biggest lever is **retention of the high-value base** — defending the customers
we already have beats chasing marginal sales. These figures are illustrative on a proxy
dataset; the **percentages scale linearly** to the retailer's revenue, and the *capabilities* are
the real deliverable.

We did this without inventing data. Where the dataset was thin (no product hierarchy, no
cost of goods, anonymous guests), we said so, engineered honest workarounds, and labelled
every assumption. That candour is the point: a data function earns trust by being right
about what it doesn't know.

---

## 2. Where we started — the "before" state

Like most retailers before a customer-data capability, the business was effectively
**flying on instruments it didn't have**:

- **No customer view.** All shoppers treated alike; no way to tell a £12k loyalist from a one-time buyer.
- **Churn discovered too late.** Lapses noticed only after the customer was long gone — and unrecoverable.
- **Marketing by gut.** Blanket promotions, discounting people who would have bought anyway, eroding margin.
- **Generic cross-sell.** No systematic "what should this customer buy next."
- **Reactive inventory.** Stocking by intuition; stockouts lose the sale *and* the basket around it.
- **13% of revenue invisible.** Guest (Non-Member) sales — large, valuable baskets — untracked and un-actionable.
- **Decisions as opinions**, not evidence; no way to measure whether an initiative actually worked.

---

## 3. What we built — the strategy

A single, coherent capability, layered:

**A trustworthy foundation.** Audited cleaning of 1.07M rows of genuinely messy data, a
**star-schema warehouse** (fact + customer/product/category/date dimensions), and a
deliberate decision to keep guest sales — labelled **Member vs Non-Member** — so nothing
is silently discarded. An LLM was used to create the product category hierarchy the raw
data lacked.

**A customer-intelligence engine** that answers three questions in sequence:
*who are our customers* (behavioural **segmentation** → six groups, three prioritised),
*who is leaving* (a **churn model** that scores risk early), and
*what should we offer them* (a **recommendation engine** for next-best product).

**A demand & availability layer** — SKU-level **forecasting** feeding a **profit-optimal
stocking** rule, so the forecast becomes an inventory decision, not just a chart.

**A value model** that prices every lever in money under explicit assumptions, so the
business can rank where to spend — and **experiments (with control groups)** to replace
assumptions with measured truth before scaling.

---

## 4. Before vs After

| Capability | Before | After (with the capability) |
|---|---|---|
| **Customer understanding** | One-size-fits-all | **6 behavioural segments**; Protect / Rescue / Grow prioritised by profit |
| **High-value base** | Undifferentiated | Identified: **17% of members drive 70% of revenue** — defend deliberately |
| **Churn** | Noticed after the fact | **Flagged early** (reliable, ranked warning); a 250-name, £0.7M-at-risk rescue list |
| **Marketing spend** | Blanket, gut-led | **Profit-thresholded targeting** + holdout controls = measured, not assumed |
| **Cross-sell** | Generic | **Personalised next-best product** (~100× better than guesswork) |
| **Inventory** | Reactive | **Demand forecast** + margin-aware stocking |
| **Guest revenue** | 13% invisible (£2.57M) | **Sized and targeted** — loyalty program converts anonymous baskets to tracked members |
| **Decision-making** | Opinion | **Evidence + a £-value model + experiments** |

---

## 5. The three plays (where the money is)

1. **Protect — the high-value base.** 70% of revenue, ~2% churn. Defend with loyalty,
   service, and a CLV-gated concierge tier — *not* discounts. The loyalty program does
   double duty: it also converts the £2.57M Non-Member base into tracked members. *Biggest lever.*
2. **Rescue — high-value, lapsing.** 250 customers worth ~£2,884 each, churning at 74% —
   ~£0.7M walking out. A one-time, personalised win-back, prioritised by the churn model and
   **proven with a control group** (the hardest, highest-attention play).
3. **Grow — the engaged mid-tier.** 1,545 customers with headroom. Cross-sell to lift ARPU,
   targeting optimised to the profit-maximising threshold and validated by a holdout.

---

## 6. The value, and how we'll prove it

The value model ranks the levers (retention largest, then availability, rescue, grow) and
frames the investment transparently. Crucially, **we do not ask the business to take the
numbers on faith** — each play ships with an experiment and an untreated control, so we
measure incremental lift and spend only where it pays back. That is the difference between
a dashboard and a decision system.

---

## 7. Risks & honest caveats (a CDO's job)

- **Proxy data.** Real client data is confidential, so this uses a public UK gift/homeware dataset as a stand-in; the *methods* transfer, the
  product mix does not. Thai-market seasonality (payday, Chinese New Year, Vegetarian
  Festival) is specified as production localisation.
- **No cost of goods.** Margin is an explicit, sensitivity-tested assumption.
- **Lost sales are unobservable**, so the availability lever is the most assumption-heavy.
- **Small cohorts limit statistical power** (the 250-person rescue test detects only large
  effects) — so we read those directionally and expand populations to gain power.
- **Simple beats complex sometimes.** On demand forecasting, a moving-average baseline
  wins the aggregate; the ML model wins 61% of SKUs — so we recommend a *hybrid*, not a
  trophy model. Knowing when not to use the fancy tool is a feature, not a failure.

---

## 8. Recommendation

Stand up the customer-intelligence capability and run the three plays in order —
**Protect, Rescue, Grow** — each behind a controlled experiment, with the value model as
the scoreboard and cohort retention as the north-star KPI. Productionise incrementally
(experiment tracking, deployment, a self-serve "ask-the-data" assistant) once the plays
prove out. The prize is not a one-off uplift; it is a business that **compounds margin by
knowing, keeping, and growing its best customers.**

*Prepared as a portfolio reference implementation. Full methodology, code, and honest
limitations: `README.md` and `docs/`.*
