"""Synthetic order and price simulator for TCA engine.

Produces a long-format DataFrame: one row per (order, timestep).
"""
import numpy as np
import pandas as pd


def simulate_orders(n_orders=200, n_steps=60, seed=42):
    rng = np.random.default_rng(seed)
    rows = []

    for order_id in range(n_orders):
        side = "buy" if rng.random() < 0.5 else "sell"
        size = int(np.exp(rng.uniform(np.log(1_000), np.log(500_000))))
        sigma_annual = rng.uniform(0.15, 0.60)          # 15%–60% annualized vol
        adv = int(rng.uniform(1e6, 5e7))                # avg daily volume
        horizon = int(rng.integers(10, n_steps + 1))    # execution window
        decision_minute = int(rng.integers(0, 390 - horizon))  # within a 6.5h day
        decision_time = pd.Timestamp("2024-01-02 09:30") + pd.Timedelta(minutes=decision_minute)

        # Convert annualized vol to per-minute vol.
        # 252 trading days * 390 min/day = 98280 minutes/year.
        sigma_min = sigma_annual / np.sqrt(252 * 390)
        sigma_bps = sigma_min * 1e4

        # Random-walk mid path with slight drift.
        mu = rng.normal(0, 0.00001)                      # per-minute drift
        shocks = rng.normal(mu, sigma_min, size=horizon)
        mid = 100.0 * np.cumprod(1.0 + shocks)

        # Spread widens with volatility (in bps).
        base_spread_bps = 1.0
        spread_bps = base_spread_bps + 0.5 * sigma_bps
        bid = mid * (1 - spread_bps / 2 / 1e4)
        ask = mid * (1 + spread_bps / 2 / 1e4)

        # Slice the order into n_slices child fills across the horizon.
        n_slices = min(10, horizon)
        slice_size = size / n_slices
        slice_idx = np.linspace(0, horizon - 1, n_slices).astype(int)

        # Square-root impact model.
        eta = 0.5
        impact_bps = eta * sigma_bps * np.sqrt(slice_size / adv)

        for t in range(horizon):
            if t in slice_idx:
                i = int(np.where(slice_idx == t)[0][0])
                imp = impact_bps
                if side == "buy":
                    fill_price = ask[t] * (1 + imp / 1e4)
                else:
                    fill_price = bid[t] * (1 - imp / 1e4)
                s_size = slice_size
            else:
                fill_price = np.nan
                s_size = 0.0
                imp = np.nan

            rows.append({
                "order_id": order_id,
                "side": side,
                "size": size,
                "sigma_annual": sigma_annual,
                "sigma_bps": sigma_bps,
                "adv": adv,
                "horizon": horizon,
                "decision_time": decision_time,
                "t": t,
                "mid": mid[t],
                "bid": bid[t],
                "ask": ask[t],
                "spread_bps": spread_bps,
                "slice_size": s_size,
                "impact_bps": imp,
                "fill_price": fill_price,
            })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = simulate_orders(n_orders=5, n_steps=20)
    print(df.head(15))
    print(df.shape)