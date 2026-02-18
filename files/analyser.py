from collections import deque
import time
from config import VOLATILITY_WINDOW, VOLATILITY_THRESHOLD, ALERT_COOLDOWN

# Store price history and last alert time for each pair
history = {}    
last_alert = {}  


def update_and_check(pair, price):
    """
    Check if price movement exceeds threshold and if we should alert.
    Returns: (should_alert, percent_move, status_message)
    """
    now = time.time()
    
    # Get or create history for this pair
    if pair not in history:
        history[pair] = deque()
    
    dq = history[pair]
    dq.append((now, price))
    
    # Remove old data points (older than 10 minutes)
    while dq and (now - dq[0][0]) > VOLATILITY_WINDOW:
        dq.popleft()
    
    # Need at least 2 data points to calculate movement
    if len(dq) < 2:
        return False, 0.0, "Building history..."
    
    # Calculate price movement from oldest to newest
    oldest_price = dq[0][1]
    percent_move = abs((price - oldest_price) / oldest_price)
    
    # Check if movement exceeds threshold
    if percent_move >= VOLATILITY_THRESHOLD:
        
        # Check if we should alert (not in cooldown period)
        prev_alert = last_alert.get(pair)
        
        if prev_alert is None:
            # First alert for this pair
            last_alert[pair] = {"time": now, "pct": percent_move}
            return True, percent_move, "First alert!"
        
        elif (now - prev_alert["time"]) > ALERT_COOLDOWN:
            # Cooldown period has passed
            last_alert[pair] = {"time": now, "pct": percent_move}
            return True, percent_move, "Cooldown expired"
        
        elif percent_move > 2 * prev_alert["pct"]:
            last_alert[pair] = {"time": now, "pct": percent_move}
            return True, percent_move, "Severity escalation!"
        
        else:
            # In cooldown 
            return False, percent_move, "In cooldown period"
    
    return False, percent_move, "Normal movement"
