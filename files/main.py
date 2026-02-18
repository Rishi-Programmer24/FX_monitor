import requests
import time
from datetime import datetime
from config import API_KEY, BASE_URL, PAIRS, CHECK_INTERVAL, VOLATILITY_THRESHOLD
from analyser import update_and_check


def fetch_price(pair_name, from_curr, to_curr):
    """
    Fetch current exchange rate from Alpha Vantage API
    Returns price as float, or None if request fails
    """
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_curr,
        "to_currency": to_curr,
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        
        # Check if we got rate limited
        if response.status_code == 429:
            print(f"  Rate limited! Waiting 60 seconds...")
            time.sleep(60)
            return None
        
        response.raise_for_status()
        data = response.json()
        # print("RAW RESPONSE:", data), Testing line to see raw API response

        
        #extract price from API response
        price = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        return price
        
    except requests.exceptions.RequestException as e:
        print(f" Network error fetching {pair_name}: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f" Error parsing response for {pair_name}: {e}")
        return None


def format_time():
    """Return current time as readable string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main monitoring loop"""

    print(" FX Monitor loading")
    print(f" Monitoring: {', '.join(PAIRS.keys())}")
    print(f"  Check interval: {CHECK_INTERVAL} seconds")
    print(f" Alert threshold: {VOLATILITY_THRESHOLD * 100:.2f}%")
    print()
    
    try:
        while True:
            print(f"\n[{format_time()}] Checking prices...")
            
            # Fetch prices for all pairs
            for pair_name, params in PAIRS.items():
                price = fetch_price(
                    pair_name,
                    params["from_currency"],
                    params["to_currency"]
                )
                
                if price is None:
                    print(f"   {pair_name}: Failed to fetch")
                    continue
                
                # Check for volatility
                should_alert, pct_move, status = update_and_check(pair_name, price)
                
                if should_alert:
                    print(f" ALERT: {pair_name} = {price:.4f} (moved {pct_move*100:.2f}%)")
                    print(f"     Reason: {status}")
                else:
                    print(f"  {pair_name} = {price:.4f} (moved {pct_move*100:.2f}%) - {status}")
            
            #wait 
            print(f"\n Sleeping for {CHECK_INTERVAL} seconds")
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n Shutting down ")
        print("=" * 60)


if __name__ == "__main__":
    main()

# print("Using API key:", API_KEY), Testing line to confirm API key is loaded correctly
