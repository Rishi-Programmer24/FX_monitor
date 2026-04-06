from io import StringIO

import pandas as pd
import requests

from fx_monitor.config import (
    API_KEY,
    BASE_URL,
    FRED_API_KEY,
    FRED_SERIES,
    GBPJPY_PAIR,
    YFINANCE_STALE_DAYS,
    YIELD_TICKERS,
)


class DataSourceError(RuntimeError):
    """Raised when a market data source cannot return usable data."""


def fetch_gbpjpy_history(
    session: requests.Session,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    params = {
        "function": "FX_DAILY",
        "from_symbol": GBPJPY_PAIR["from_currency"],
        "to_symbol": GBPJPY_PAIR["to_currency"],
        "outputsize": "full",
        "apikey": API_KEY,
    }

    response = session.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "Error Message" in payload:
        raise DataSourceError(payload["Error Message"])

    if "Note" in payload or "Information" in payload:
        raise DataSourceError(payload.get("Note") or payload.get("Information"))

    series = payload.get("Time Series FX (Daily)")
    if not series:
        raise DataSourceError("Alpha Vantage did not return FX_DAILY history.")

    frame = (
        pd.DataFrame.from_dict(series, orient="index")
        .rename(columns={"4. close": GBPJPY_PAIR["name"]})
        [[GBPJPY_PAIR["name"]]]
    )
    frame.index = pd.to_datetime(frame.index)
    frame[GBPJPY_PAIR["name"]] = pd.to_numeric(frame[GBPJPY_PAIR["name"]], errors="coerce")
    frame = frame.sort_index()
    return frame.loc[start_date:end_date]


def _fetch_yfinance_yield_series(
    ticker: str,
    column_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as error:
        raise DataSourceError("yfinance is not installed.") from error

    dataset = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if dataset.empty or "Close" not in dataset.columns:
        if hasattr(dataset.columns, "get_level_values") and "Close" in dataset.columns.get_level_values(0):
            dataset.columns = dataset.columns.get_level_values(0)
        else:
            raise DataSourceError(f"yfinance returned no close prices for {ticker}.")

    series = dataset["Close"].copy()
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    series.index = pd.to_datetime(series.index)
    if getattr(series.index, "tz", None) is not None:
        series.index = series.index.tz_localize(None)
    series = pd.to_numeric(series, errors="coerce").dropna()

    if series.empty:
        raise DataSourceError(f"yfinance returned only missing values for {ticker}.")

    latest_expected = pd.Timestamp(end_date) - pd.Timedelta(days=YFINANCE_STALE_DAYS)
    if series.index.max() < latest_expected:
        raise DataSourceError(
            f"{ticker} looks stale on yfinance; last observation is {series.index.max().date()}."
        )

    return series.to_frame(name=column_name)


def _fetch_fred_yield_series(
    series_id: str,
    column_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    series = None

    if FRED_API_KEY:
        try:
            from fredapi import Fred
        except ImportError as error:
            raise DataSourceError("fredapi is not installed.") from error

        fred = Fred(api_key=FRED_API_KEY)
        series = fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
        )
    else:
        response = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": series_id, "cosd": start_date, "coed": end_date},
            timeout=30,
        )
        response.raise_for_status()

        frame = pd.read_csv(
            StringIO(response.text),
            parse_dates=["observation_date"],
        ).rename(columns={"observation_date": "Date", series_id: column_name})
        frame = frame.set_index("Date")
        frame[column_name] = pd.to_numeric(frame[column_name], errors="coerce")
        frame = frame.dropna()

        if frame.empty:
            raise DataSourceError(f"FRED returned no usable observations for {series_id}.")

        return frame

    if series.empty:
        raise DataSourceError(f"FRED returned no observations for {series_id}.")

    frame = pd.DataFrame(series, columns=[column_name])
    frame.index = pd.to_datetime(frame.index)
    frame[column_name] = pd.to_numeric(frame[column_name], errors="coerce")
    frame = frame.dropna()

    if frame.empty:
        raise DataSourceError(f"FRED returned only missing values for {series_id}.")

    return frame


def fetch_bond_yield_history(
    country_code: str,
    start_date: str,
    end_date: str,
):
    column_name = f"{country_code}_10Y"
    ticker = YIELD_TICKERS[column_name]
    fred_series = FRED_SERIES[column_name]

    try:
        frame = _fetch_yfinance_yield_series(
            ticker=ticker,
            column_name=column_name,
            start_date=start_date,
            end_date=end_date,
        )
        return frame, f"yfinance:{ticker}"
    except DataSourceError as yfinance_error:
        frame = _fetch_fred_yield_series(
            series_id=fred_series,
            column_name=column_name,
            start_date=start_date,
            end_date=end_date,
        )
        return frame, f"fred:{fred_series} (fallback after {yfinance_error})"
