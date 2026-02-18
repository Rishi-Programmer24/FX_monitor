# FX Monitor - Version 1

A foreign exchange rate monitoring system that alerts you when currency pairs move significantly. This is my first full attempt at this project, and am planning to correct errors and add more features to it in version 2.

## What This Does

- Fetches live EUR/USD and GBP/USD exchange rates every 60 seconds
- Tracks price movements over a 10-minute rolling window
- Alerts you when volatility exceeds 0.5% 
- Prevents alert spam with a 5-minute cooldown period

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get the Free API Key

1. Go to https://www.alphavantage.co/support/#api-key

### 3. Configure

Create a `.env` file in the project root:

```
API_KEY= ...
```

### 4. Run

```bash
python -m src.fx_monitor.main
```

