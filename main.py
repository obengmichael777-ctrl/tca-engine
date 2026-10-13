"""Entry point: simulate, compute TCA, print report, save charts."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

from simulator import simulate_orders
from tca import compute_tca, summary_table

OUT = Path("output")
OUT.mkdir(exist_ok=True)


def main():
    print("Simulating orders...")
    raw = simulate_orders(n_orders=300, n_steps=60, seed=7)

    print("Computing TCA...")
    orders = compute_tca(raw)
    orders.to_csv(OUT / "orders.csv", index=False)

    by_size, by_vol = summary_table(orders)
    by_size.to_csv(OUT / "summary_by_size.csv")
    by_vol.to_csv(OUT / "summary_by_vol.csv")

    print("\n=== Overall ===")
    print(orders[["shortfall_bps", "spread_cost_bps",
                  "impact_bps", "timing_bps"]].mean().round(2).to_string())

    print("\n=== By size bucket ===")
    print(by_size.to_string())

    print("\n=== By vol regime ===")
    print(by_vol.to_string())

    # --- Chart 1: shortfall by size bucket ---
    ax = by_size["shortfall_bps"].plot(kind="bar", color="steelblue",
                                       title="Shortfall by size bucket (bps)")
    ax.set_ylabel("bps")
    plt.tight_layout()
    plt.savefig(OUT / "shortfall_by_size.png", dpi=120)
    plt.close()

    # --- Chart 2: shortfall by vol regime ---
    ax = by_vol["shortfall_bps"].plot(kind="bar", color="indianred",
                                      title="Shortfall by volatility regime (bps)")
    ax.set_ylabel("bps")
    plt.tight_layout()
    plt.savefig(OUT / "shortfall_by_vol.png", dpi=120)
    plt.close()

    # --- Chart 3: stacked decomposition by size bucket ---
    ax = by_size[["spread_cost_bps", "impact_bps", "timing_bps"]].plot(
        kind="bar", stacked=True, title="Shortfall decomposition by size bucket"
    )
    ax.set_ylabel("bps")
    plt.tight_layout()
    plt.savefig(OUT / "decomposition_by_size.png", dpi=120)
    plt.close()

    print(f"\nWrote {len(list(OUT.glob('*.png')))} charts and CSVs to {OUT}/")


if __name__ == "__main__":
    main()