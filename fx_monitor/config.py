import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

# Monitoring Settings
CHECK_INTERVAL = 60          # Seconds between checks (demo-friendly; may exceed free API daily quota)
VOLATILITY_WINDOW = 600      # 10 minutes rolling window
VOLATILITY_THRESHOLD = 0.005 # 0.5% movement triggers alert
ALERT_COOLDOWN = 300         # 5 minutes silence after alert

# Currency Pairs to Monitor
PAIRS = {
    "EURUSD": {"from_currency": "EUR", "to_currency": "USD"},
    "GBPUSD": {"from_currency": "GBP", "to_currency": "USD"}
}
