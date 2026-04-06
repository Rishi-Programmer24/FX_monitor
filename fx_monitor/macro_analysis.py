from pathlib import Path

import pandas as pd
import requests

from fx_monitor.config import DEFAULT_OUTPUT_DIR, GBPJPY_PAIR
from fx_monitor.data_sources import fetch_bond_yield_history, fetch_gbpjpy_history
from fx_monitor.events import get_events_in_range
from fx_monitor.plotting import plot_macro_divergence


def build_macro_dataset(start_date: str, end_date: str, rolling_window: int):
    with requests.Session() as session:
        fx_frame = fetch_gbpjpy_history(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

    uk_frame, uk_source = fetch_bond_yield_history(
        country_code="UK",
        start_date=start_date,
        end_date=end_date,
    )
    jp_frame, jp_source = fetch_bond_yield_history(
        country_code="JP",
        start_date=start_date,
        end_date=end_date,
    )

    dataset = pd.concat([fx_frame, uk_frame, jp_frame], axis=1).sort_index()
    business_days = pd.date_range(dataset.index.min(), dataset.index.max(), freq="B")
    dataset = dataset.reindex(business_days).ffill().dropna()
    dataset.index.name = "Date"

    dataset["Spread"] = dataset["UK_10Y"] - dataset["JP_10Y"]
    corr_col = f"Rolling_Corr_{rolling_window}D"
    dataset[corr_col] = dataset["Spread"].rolling(window=rolling_window).corr(
        dataset[GBPJPY_PAIR["name"]]
    )

    spread_std = dataset["Spread"].rolling(window=rolling_window).std()
    fx_std = dataset[GBPJPY_PAIR["name"]].rolling(window=rolling_window).std()
    zero_variance_mask = (spread_std <= 1e-12) | (fx_std <= 1e-12)
    dataset.loc[zero_variance_mask, corr_col] = pd.NA

    return dataset, {"UK_10Y": uk_source, "JP_10Y": jp_source}


def summarise_macro_dataset(dataset: pd.DataFrame, rolling_window: int):
    corr_col = f"Rolling_Corr_{rolling_window}D"
    clean_corr = pd.to_numeric(dataset[corr_col], errors="coerce").dropna()

    if clean_corr.empty:
        raise ValueError(
            f"Not enough observations to calculate a {rolling_window}-day rolling correlation."
        )

    latest = dataset.iloc[-1]
    latest_corr_date = clean_corr.index[-1].date().isoformat()
    strongest_positive_date = clean_corr.idxmax().date().isoformat()
    strongest_negative_date = clean_corr.idxmin().date().isoformat()
    fx_return = (
        (dataset[GBPJPY_PAIR["name"]].iloc[-1] / dataset[GBPJPY_PAIR["name"]].iloc[0]) - 1
    ) * 100

    return {
        "start_date": dataset.index.min().date().isoformat(),
        "end_date": dataset.index.max().date().isoformat(),
        "latest_fx": float(latest[GBPJPY_PAIR["name"]]),
        "latest_spread": float(latest["Spread"]),
        "latest_corr": float(clean_corr.iloc[-1]),
        "latest_corr_date": latest_corr_date,
        "max_corr": float(clean_corr.max()),
        "max_corr_date": strongest_positive_date,
        "min_corr": float(clean_corr.min()),
        "min_corr_date": strongest_negative_date,
        "fx_return_pct": float(fx_return),
        "avg_corr": float(clean_corr.mean()),
    }


def build_readme_finding(summary: dict, rolling_window: int) -> str:
    return (
        f"Between {summary['start_date']} and {summary['end_date']}, GBP/JPY rose "
        f"{summary['fx_return_pct']:.1f}% while the UK-Japan 10Y yield spread ended at "
        f"{summary['latest_spread']:.2f} percentage points. Over the same sample, the "
        f"{rolling_window}-day rolling correlation between the spread and GBP/JPY averaged "
        f"{summary['avg_corr']:.2f}; the latest valid reading was {summary['latest_corr']:.2f} "
        f"on {summary['latest_corr_date']}, it peaked at {summary['max_corr']:.2f} on "
        f"{summary['max_corr_date']}, and fell to {summary['min_corr']:.2f} on "
        f"{summary['min_corr_date']}, showing that monetary-policy divergence was a strong "
        "driver of the cross for long stretches, but not continuously."
    )


def run_macro_tracker(
    start_date: str,
    end_date: str,
    rolling_window: int,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    save_plot: bool = True,
):
    dataset, sources = build_macro_dataset(
        start_date=start_date,
        end_date=end_date,
        rolling_window=rolling_window,
    )
    summary = summarise_macro_dataset(dataset=dataset, rolling_window=rolling_window)
    events = get_events_in_range(start_date=start_date, end_date=end_date)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "gbpjpy_macro_divergence.csv"
    dataset.to_csv(csv_path)

    plot_path = output_path / "gbpjpy_macro_divergence.png"
    if save_plot:
        plot_macro_divergence(
            dataset=dataset,
            events=events,
            rolling_window=rolling_window,
            output_path=plot_path,
        )

    return {
        "dataset": dataset,
        "sources": sources,
        "summary": summary,
        "finding": build_readme_finding(summary=summary, rolling_window=rolling_window),
        "csv_path": csv_path,
        "plot_path": plot_path if save_plot else None,
    }
