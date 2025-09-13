# --- Setup and Execution ---
# 1. Install the required library:
#    pip install kiteconnect
#
# 2. Fill in your `api_key` and `access_token` in the "User Configuration" section below.
#
# 3. Run the script from your terminal:
#    python trading_bot.py
#
# 4. The script will prompt you to enter the Nifty 50 strike price and option type (CE/PE).

import logging
from kiteconnect import KiteConnect, KiteTicker
import sys

# --- User Configuration ---
# 1. Login to kite.zerodha.com and generate a request_token.
# 2. Use the following script to generate an access_token:
#    (This needs to be done once a day)
#
# from kiteconnect import KiteConnect
#
# api_key = "YOUR_API_KEY"
# api_secret = "YOUR_API_SECRET"
# request_token = "YOUR_REQUEST_TOKEN"
#
# kite = KiteConnect(api_key=api_key)
# data = kite.generate_session(request_token, api_secret=api_secret)
#
# print(f"access_token = '{data['access_token']}'")

api_key = "YOUR_API_KEY"
access_token = "YOUR_ACCESS_TOKEN"

# --- Main Trading Logic ---

def main():
    """
    Main function to run the trading bot.
    """
    logging.basicConfig(level=logging.INFO)

    # Initialize KiteConnect
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info("Successfully connected to Kite API.")
    except Exception as e:
        logging.error(f"Authentication failed: {e}")
        sys.exit(1)

    # Get user input for strike price
    try:
        strike_price_input = input("Enter the Nifty 50 strike price (e.g., 22500): ")
        strike_price = int(strike_price_input)
        option_type = input("Enter option type (CE or PE): ").upper()
        if option_type not in ["CE", "PE"]:
            raise ValueError("Invalid option type. Please enter CE or PE.")
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        sys.exit(1)

    logging.info(f"Looking for Nifty 50 {strike_price} {option_type}...")

    # Find the instrument token for the Nifty 50 option
    instrument_token = None
    try:
        instruments = kite.instruments("NFO")
        for instrument in instruments:
            if (instrument['name'] == 'NIFTY' and
                instrument['strike'] == strike_price and
                instrument['instrument_type'] == option_type and
                instrument['segment'] == 'NFO-OPT'):
                # We will take the nearest expiry for simplicity
                instrument_token = instrument['instrument_token']
                logging.info(f"Found instrument: {instrument['tradingsymbol']}")
                break
    except Exception as e:
        logging.error(f"Error fetching instruments: {e}")
        sys.exit(1)

    if not instrument_token:
        logging.error("Could not find the instrument for the given strike price.")
        sys.exit(1)

    # Setup WebSocket
    kws = KiteTicker(api_key, access_token)

    # Add a simple alert sound
    try:
        import winsound
        def play_alert():
            winsound.Beep(1000, 500)  # Frequency 1000 Hz, duration 500 ms
    except ImportError:
        def play_alert():
            # Fallback for non-Windows systems
            print("\007") # Bell character

    # State management
    alert_triggered = False
    entry_price = None

    def on_ticks(ws, ticks):
        nonlocal alert_triggered, entry_price
        for tick in ticks:
            if tick['instrument_token'] == instrument_token:
                ltp = tick['last_price']
                logging.info(f"LTP for {instrument['tradingsymbol']}: {ltp}")

                # Alert at 95
                if 94.5 <= ltp <= 95.5 and not alert_triggered:
                    logging.info("Price is around 95! Playing alert.")
                    play_alert()
                    alert_triggered = True

                # Entry at 100
                if ltp >= 100 and entry_price is None:
                    entry_price = 100
                    logging.info(f"--- ENTRY TRIGGERED at {entry_price} ---")

                # Stop-loss and Target
                if entry_price is not None:
                    # Stop-loss at 96
                    if ltp <= 96:
                        logging.warning(f"--- STOP-LOSS HIT at {ltp} ---")
                        ws.close()
                    # Target at 109
                    elif ltp >= 109:
                        logging.info(f"--- TARGET REACHED at {ltp} ---")
                        ws.close()

    def on_connect(ws, response):
        logging.info("WebSocket connected. Subscribing to ticks.")
        ws.subscribe([instrument_token])
        ws.set_mode(ws.MODE_FULL, [instrument_token])

    def on_close(ws, code, reason):
        logging.info(f"WebSocket closed: {code} - {reason}")

    # Assign callbacks
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    # Start the WebSocket connection
    kws.connect(threaded=True)

if __name__ == "__main__":
    main()
