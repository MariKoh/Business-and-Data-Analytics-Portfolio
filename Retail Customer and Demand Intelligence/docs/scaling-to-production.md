# Scaling to Production

> **Placeholder — completed in Session 6.**

This document will explain how the project scales to the retailer's real volume:

- **Data processing at scale** — where PySpark / Databricks replace pandas for
  billions of transaction lines.
- **Model lifecycle** — an MLflow Model Registry (and/or Azure ML) for staging,
  promotion, and rollback.
- **Feature store** — serving the same features to training and inference.
- **Orchestration** — Airflow (or n8n) scheduling the retraining loop.
- **Modelling choice** — the deliberate decision to use classical / gradient-
  boosting models over deep learning for these tabular problems, with reasoning.
- **Data governance & PDPA** — pseudonymization of Clubcard data, consent and
  retention handling, and restricting the GenAI assistant from surfacing PII.
