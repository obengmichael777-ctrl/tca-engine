# TCA Engine

A small Python engine that measures execution quality of simulated equity
orders against standard benchmarks (arrival, VWAP, TWAP, close) and decomposes
execution shortfall into spread cost, market impact, and timing risk.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Output

- `output/orders.csv` — per-order TCA metrics
- `output/summary_by_size.csv`, `output/summary_by_vol.csv` — aggregated tables
- `output/shortfall_by_size.png`
- `output/shortfall_by_vol.png`
- `output/decomposition_by_size.png`

## What I learned

- **Execution shortfall** is the cost of trading away from a benchmark,
  expressed in basis points. Sign convention: positive = cost, for both buys
  and sells.
- **Perold's decomposition** splits shortfall into spread + impact + timing.
  Spread is the half-spread you cross; impact is your own footprint; timing
  is the price drift you didn't cause.
- **Square-root impact**: market impact scales with `sigma * sqrt(size/ADV)`,
  not linearly with size. This is one of the most robust empirical facts in
  microstructure.
- **Volatility scaling**: over `dt` time, price std dev scales with
  `sqrt(dt)`, not `dt`. Getting this wrong makes synthetic paths look wrong.
- **Segmentation matters**: aggregating by size bucket and volatility regime
  shows that impact dominates for large orders and timing dominates in
  high-vol regimes.