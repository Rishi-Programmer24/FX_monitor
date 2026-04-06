import argparse

from fx_monitor.config import (
    DEFAULT_END_DATE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_ROLLING_WINDOW,
    DEFAULT_START_DATE,
)
from fx_monitor.live_monitor import run_live_monitor
from fx_monitor.macro_analysis import run_macro_tracker


def parse_args():
    parser = argparse.ArgumentParser(
        description="FX Monitor toolkit for live volatility alerts and macro divergence analysis."
    )
    subparsers = parser.add_subparsers(dest="command")

    live_parser = subparsers.add_parser("live", help="Run the real-time FX volatility monitor.")
    live_parser.set_defaults(command="live")

    macro_parser = subparsers.add_parser(
        "macro",
        help="Run the East-West Macro Divergence Tracker for GBP/JPY and 10Y yields.",
    )
    macro_parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    macro_parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    macro_parser.add_argument("--window", type=int, default=DEFAULT_ROLLING_WINDOW)
    macro_parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    macro_parser.add_argument(
        "--skip-plot",
        action="store_true",
        help="Save the merged dataset without rendering the chart.",
    )
    macro_parser.set_defaults(command="macro")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command in (None, "live"):
        run_live_monitor()
        return

    result = run_macro_tracker(
        start_date=args.start_date,
        end_date=args.end_date,
        rolling_window=args.window,
        output_dir=args.output_dir,
        save_plot=not args.skip_plot,
    )

    summary = result["summary"]
    print("East-West Macro Divergence Tracker")
    print(f"Sample: {summary['start_date']} to {summary['end_date']}")
    print(f"Latest GBP/JPY: {summary['latest_fx']:.2f}")
    print(f"Latest UK-Japan 10Y spread: {summary['latest_spread']:.2f} percentage points")
    print(
        f"Latest valid {args.window}D rolling correlation: "
        f"{summary['latest_corr']:.2f} (as of {summary['latest_corr_date']})"
    )
    print(f"Dataset saved to: {result['csv_path']}")
    if result["plot_path"] is not None:
        print(f"Chart saved to: {result['plot_path']}")
    print(f"Yield sources: {result['sources']}")
    print(result["finding"])


if __name__ == "__main__":
    main()
