# Per-Segment Behavioural EDA (Analysis 1 deep-dive)
Behaviour beyond RFMTC means — basket habits, cadence, repeat rate, price point, and category spend mix. Source: model_transactions + customer_features + category_map.

## Behavioural profile
```
                              members  avg_spend  avg_freq  recency_days  tenure_days  basket_value  items_per_basket  distinct_skus  pct_repeat  cadence_days  churn  avg_unit_price
segment                                                                                                                                                                              
High-value, active               1013    11790.6      20.8          34.6        661.8         603.9             371.5          219.1       100.0          45.5    0.0            2.93
High-value, lapsing, at-risk      250     2884.4       7.0         483.9        618.7         396.0             382.3           74.4       100.0          27.5    0.7            3.07
Mid-value, active, at-risk       1545     1700.9       5.1          83.9        548.5         371.6             273.2           86.2       100.0         122.6    0.0            2.92
Mid-value, lapsing, at-risk       675      833.9       2.9         388.4        580.3         286.6             166.0           48.1       100.0          96.5    0.3            3.11
Low-value, active                1380      655.9       2.0          83.0        144.3         342.4             212.7           39.2        50.0          46.8    0.0            2.81
Low-value, lapsing                989      311.2       1.0         514.9        516.2         302.0             193.4           20.9         0.0           0.0    0.0            3.04
```

## Top categories per segment
- **High-value, active** — Kitchen & Dining 18%, Home Decor 17%, Storage & Organisation 11%
- **High-value, lapsing, at-risk** — Kitchen & Dining 18%, Home Decor 17%, Storage & Organisation 10%
- **Mid-value, active, at-risk** — Kitchen & Dining 18%, Home Decor 15%, Storage & Organisation 11%
- **Mid-value, lapsing, at-risk** — Kitchen & Dining 18%, Home Decor 15%, Storage & Organisation 11%
- **Low-value, active** — Kitchen & Dining 19%, Home Decor 17%, Storage & Organisation 10%
- **Low-value, lapsing** — Kitchen & Dining 20%, Home Decor 13%, Other 12%

Full matrix: `reports/tables/segment_category_mix.csv` | heatmap: `reports/figures/seg_category_heatmap.png`
