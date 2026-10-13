"""Transaction cost analysis: benchmarks, shortfall, and decomposition."""
import numpy as np
import pandas as pd


def compute_tca(df: pd.DataFrame) -> pd.DataFrame:
    """Given long-format sim data, return one row per order with TCA metrics."""
    records = []

    for order_id, g in df.groupby("order_id", sort=False):
        g = g.sort_values("t")
        side = g["side"].iloc[0]
        size = g["size"].iloc[0]
        sigma_bps = g["sigma_bps"].iloc[0]
        horizon = g["horizon"].iloc[0]
        decision_time = g["decision_time"].iloc[0]

        # --- Benchmarks ---
        arrival = g["mid"].iloc[0]
        twap = g["mid"].mean()
        # VWAP weighted by slice_size (falls back to TWAP where no fill)
        weights = g["slice_size"].values
        if weights.sum() > 0:
            vwap = np.average(g["mid"].values, weights=weights)
        else:
            vwap = twap
        close = g["mid"].iloc[-1]

        # --- Actual execution ---
        fills = g[g["slice_size"] > 0]
        if len(fills) == 0:
            continue
        exec_w = fills["slice_size"].values
        avg_exec = np.average(fills["fill_price"].values, weights=exec_w)

        # --- Shortfall vs arrival (sign-aware) ---
        if side == "buy":
            shortfall_bps = 1e4 * (avg_exec - arrival) / arrival
        else:
            shortfall_bps = 1e4 * (arrival - avg_exec) / arrival

        # --- Decomposition ---
        # Spread cost: half-spread paid on each fill (size-weighted)
        half_spread_bps = g["spread_bps"].iloc[0] / 2.0
        spread_cost_bps = half_spread_bps  # same for all slices

        # Impact: size-weighted impact from simulator (ground truth)
        impact_bps = np.average(fills["impact_bps"].values, weights=exec_w)

        # Timing: the residual
        timing_bps = shortfall_bps - spread_cost_bps - impact_bps

        records.append({
            "order_id": order_id,
            "side": side,
            "size": size,
            "sigma_bps": sigma_bps,
            "horizon": horizon,
            "decision_time": decision_time,
            "arrival": arrival,
            "twap": twap,
            "vwap": vwap,
            "close": close,
            "avg_exec": avg_exec,
            "shortfall_bps": shortfall_bps,
            "spread_cost_bps": spread_cost_bps,
            "impact_bps": impact_bps,
            "timing_bps": timing_bps,
        })

    out = pd.DataFrame(records)

    # --- Buckets for aggregation ---
    out["size_bucket"] = pd.qcut(out["size"], 4,
                                 labels=["XS", "S", "M", "L"],
                                 duplicates="drop")
    out["vol_regime"] = pd.qcut(out["sigma_bps"], 3,
                                labels=["low", "med", "high"],
                                duplicates="drop")
    out["hour"] = out["decision_time"].dt.hour

    return out


def summary_table(orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate shortfall and components by size bucket and vol regime."""
    by_size = orders.groupby("size_bucket", observed=True)[
        ["shortfall_bps", "spread_cost_bps", "impact_bps", "timing_bps"]
    ].mean().round(2)
    by_size.index = pd.Index(by_size.index, name="size_bucket")

    by_vol = orders.groupby("vol_regime", observed=True)[
        ["shortfall_bps", "spread_cost_bps", "impact_bps", "timing_bps"]
    ].mean().round(2)
    by_vol.index = pd.Index(by_vol.index, name="vol_regime")

    return by_size, by_vol