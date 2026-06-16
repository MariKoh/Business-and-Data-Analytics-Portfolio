# Architecture

One repository that turns raw omnichannel transactions into business decisions, in five
layers. Business leads; every model maps to a profit decision.

```mermaid
flowchart LR
    raw[("Online Retail II\nraw .xlsx")] --> clean["Cleaning\nsrc/data/clean.py"]
    clean --> ct["clean_transactions\n(analytics, guest-inclusive)"]
    clean --> mt["model_transactions\n(modelling, Member/Non-Member)"]
    ct --> wh["Star-schema warehouse\nfact_sales + dim_*"]
    ct --> feat["Feature foundation\nsrc/features"]
    mt --> feat
    feat --> seg["A1 Segmentation\n(RFMTC + K-Means)"]
    feat --> churn["A2 Churn + cohorts\n(XGBoost, AUC)"]
    feat --> xs["A3 Cross-sell\n(item-based CF)"]
    feat --> fc["A4 Forecast\n(XGBoost + newsvendor)"]
    seg --> val["Value model\n(£ per lever)"]
    churn --> val
    xs --> val
    fc --> val
    val --> rep["Executive report + decks"]
```

**Layers:** (1) cleaning → two fit-for-purpose tables; (2) a star-schema warehouse and a
reusable feature foundation (with an LLM-built product-category dimension); (3) four ML
analyses; (4) a £-value model ranking the levers; (5) an executive report and two
audience-tailored decks. Productionisation (experiment tracking, containerised serving, a
GenAI "ask-the-data" assistant) is the documented roadmap — see
[`scaling-to-production.md`](scaling-to-production.md). Warehouse ER diagram:
[`star_schema.md`](star_schema.md).
