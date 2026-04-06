import os
from datetime import date

from dotenv import load_dotenv

load_dotenv()

# API configuration
API_KEY = os.getenv("API_KEY", "demo")
FRED_API_KEY = os.getenv("FRED_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Live monitor settings
CHECK_INTERVAL = 60           # Seconds between checks
VOLATILITY_WINDOW = 600       # 10 minutes rolling window
VOLATILITY_THRESHOLD = 0.005  # 0.5% movement triggers alert
ALERT_COOLDOWN = 300          # 5 minutes silence after alert

# Currency pairs for the live monitor
PAIRS = {
    "EURUSD": {"from_currency": "EUR", "to_currency": "USD"},
    "GBPUSD": {"from_currency": "GBP", "to_currency": "USD"},
}

# Macro divergence tracker settings
DEFAULT_START_DATE = os.getenv("MACRO_START_DATE", "2021-01-01")
DEFAULT_END_DATE = os.getenv("MACRO_END_DATE", date.today().isoformat())
DEFAULT_ROLLING_WINDOW = int(os.getenv("MACRO_ROLLING_WINDOW", "60"))
DEFAULT_OUTPUT_DIR = os.getenv("MACRO_OUTPUT_DIR", "outputs")
YFINANCE_STALE_DAYS = int(os.getenv("YFINANCE_STALE_DAYS", "14"))

GBPJPY_PAIR = {
    "name": "GBP_JPY",
    "from_currency": "GBP",
    "to_currency": "JPY",
}

YIELD_TICKERS = {
    "UK_10Y": "GB10Y=RR",
    "JP_10Y": "JP10Y=RR",
}

FRED_SERIES = {
    "UK_10Y": "IRLTLT01GBM156N",
    "JP_10Y": "IRLTLT01JPM156N",
}
