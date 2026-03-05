import time
from datetime import datetime

import requests

from fx_monitor.config import (
    API_KEY,
    BASE_URL,
    PAIRS,
    CHECK_INTERVAL,
    VOLATILITY_THRESHOLD,
)
from fx_monitor.analyser import update_and_check


def fetch_price(session: requests.Session, pair_name: str, from_curr: str, to_curr: str, retries: int = 3):
    """
    Pull the current exchange rate from Alpha Vantage.
    Returns the rate as a float, or None if something went wrong.

    Note: Alpha Vantage doesn't always use HTTP 429 for throttling - sometimes
    it just returns a 200 with a "Note" or "Information" field in the JSON instead.
    """
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_curr,
        "to_currency": to_curr,
        "apikey": API_KEY,
    }

    for attempt in range(1, retries + 1):
        try:
            response = session.get(BASE_URL, params=params, timeout=10)

            if response.status_code == 429:
                print(f"  Rate limited on {pair_name}, waiting 60 seconds")
                time.sleep(60)
                continue

            response.raise_for_status()
            data = response.json()

            # Alpha Vantage hides throttle messages in the response body
            if isinstance(data, dict) and ("Note" in data or "Information" in data):
                msg = data.get("Note") or data.get("Information")
                print(f"  API message for {pair_name}: {msg}")
                time.sleep(60)
                continue

            if isinstance(data, dict) and ("Error Message" in data):
                print(f"  API error for {pair_name}: {data.get('Error Message')}")
                return None

            price = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            return price

        except requests.exceptions.RequestException as e:
            print(f"  Network error on {pair_name} (attempt {attempt}/{retries}): {e}")
            # back off a bit before retrying: 1s, 2s, 4s
            time.sleep(2 ** (attempt - 1))
        except (KeyError, ValueError, TypeError) as e:
            print(f"  Couldn't parse response for {pair_name}: {e}")
            return None

    return None


def format_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    print("=" * 60)
    print(" FX Monitor")
    print(f" Watching: {', '.join(PAIRS.keys())}")
    print(f" Checking every {CHECK_INTERVAL} seconds")
    print(f" Alert threshold: {VOLATILITY_THRESHOLD * 100:.2f}%")
    print("=" * 60)
    print()

    session = requests.Session()

    try:
        while True:
            print(f"\n[{format_time()}] Checking prices")

            for pair_name, params in PAIRS.items():
                price = fetch_price(
                    session=session,
                    pair_name=pair_name,
                    from_curr=params["from_currency"],
                    to_curr=params["to_currency"],
                )

                if price is None:
                    print(f"  {pair_name}: failed to fetch")
                    continue

                should_alert, pct_move, status = update_and_check(pair_name, price)

                if should_alert:
                    print(f"  ALERT: {pair_name} = {price:.4f} (moved {pct_move*100:.2f}%)")
                    print(f"  Reason: {status}")
                else:
                    print(f"  {pair_name} = {price:.4f} (moved {pct_move*100:.2f}%) - {status}")

            print(f"\n  Next check in {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        pass
    finally:
        session.close()
        print("\n Shutting down")
        print("=" * 60)


if __name__ == "__main__":
    main()
