from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from fx_monitor.config import GBPJPY_PAIR


def _nearest_index(target_date: pd.Timestamp, index: pd.Index) -> pd.Timestamp:
    position = index.get_indexer([target_date], method="nearest")[0]
    return index[position]


def plot_macro_divergence(
    dataset: pd.DataFrame,
    events: list[dict],
    rolling_window: int,
    output_path: Path,
):
    plt.style.use("seaborn-v0_8-whitegrid")

    figure, (price_axis, corr_axis) = plt.subplots(
        2,
        1,
        figsize=(15, 10),
        sharex=True,
        gridspec_kw={"height_ratios": [2.4, 1]},
    )

    spread_axis = price_axis.twinx()
    corr_column = f"Rolling_Corr_{rolling_window}D"

    price_line = price_axis.plot(
        dataset.index,
        dataset[GBPJPY_PAIR["name"]],
        color="#0b4f6c",
        linewidth=2.2,
        label="GBP/JPY",
    )
    spread_line = spread_axis.plot(
        dataset.index,
        dataset["Spread"],
        color="#d17a22",
        linewidth=2,
        linestyle="--",
        label="UK 10Y - Japan 10Y spread",
    )

    price_axis.set_title("East-West Macro Divergence Tracker: GBP/JPY vs UK-Japan 10Y Spread")
    price_axis.set_ylabel("GBP/JPY")
    spread_axis.set_ylabel("Yield Spread (%)")

    for idx, event in enumerate(events):
        event_date = _nearest_index(pd.Timestamp(event["date"]), dataset.index)
        event_price = dataset.loc[event_date, GBPJPY_PAIR["name"]]
        y_offset = 18 if idx % 2 == 0 else -26

        price_axis.axvline(event_date, color=event["color"], alpha=0.18, linewidth=1)
        price_axis.annotate(
            event["label"],
            xy=(event_date, event_price),
            xytext=(0, y_offset),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=event["color"],
            arrowprops={"arrowstyle": "-", "color": event["color"], "lw": 0.8},
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": event["color"], "alpha": 0.75},
        )

    combined_lines = price_line + spread_line
    price_axis.legend(
        combined_lines,
        [line.get_label() for line in combined_lines],
        loc="upper left",
    )

    corr_axis.plot(
        dataset.index,
        dataset[corr_column],
        color="#3a7d44",
        linewidth=2,
    )
    corr_axis.axhline(0, color="black", linewidth=0.8, alpha=0.7)
    corr_axis.axhline(0.5, color="#888888", linewidth=0.7, linestyle=":", alpha=0.8)
    corr_axis.axhline(-0.5, color="#888888", linewidth=0.7, linestyle=":", alpha=0.8)
    corr_axis.set_ylabel(f"{rolling_window}D Corr")
    corr_axis.set_xlabel("Date")
    corr_axis.set_title(f"{rolling_window}-Day Rolling Correlation: Yield Spread vs GBP/JPY")

    corr_axis.xaxis.set_major_locator(mdates.YearLocator())
    corr_axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)
