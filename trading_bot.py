# --- Setup and Execution ---
# 1. Install the required library:
#    pip install kiteconnect
#
# 2. Open `config_live.ini` and fill in your details:
#    - [KITE]: `api_key` and `access_token`
#    - [TRADING]: `instrument_name`, `strike_price`, `option_type`, and other trading parameters.
#
# 3. Run the script from your terminal:
#    python trading_bot.py

import logging
from kiteconnect import KiteConnect, KiteTicker
import sys
import configparser

# --- Configuration is now in config.ini ---

# --- Main Trading Logic ---

def main():
    """
    Main function to run the trading bot.
    """
    logging.basicConfig(level=logging.INFO)

    # Read configuration
    config = configparser.ConfigParser()
    try:
        if not config.read('config_live.ini'):
            logging.error("Could not read config_live.ini. Please make sure the file exists.")
            sys.exit(1)

        api_key = config.get('KITE', 'api_key')
        access_token = config.get('KITE', 'access_token')

        # Trading parameters
        instrument_name = config.get('TRADING', 'instrument_name')
        strike_price = config.getint('TRADING', 'strike_price')
        option_type = config.get('TRADING', 'option_type').upper()
        alert_price = config.getfloat('TRADING', 'alert_price')
        entry_price_target = config.getfloat('TRADING', 'entry_price')
        stop_loss_price = config.getfloat('TRADING', 'stop_loss_price')
        target_price = config.getfloat('TRADING', 'target_price')

        if option_type not in ["CE", "PE"]:
            raise ValueError("Invalid option_type in config.ini. Must be CE or PE.")

    except (KeyError, configparser.NoSectionError, ValueError) as e:
        logging.error(f"Error reading config.ini: {e}. Make sure [KITE] and [TRADING] sections are correctly set up with valid numbers.")
        sys.exit(1)

    # Initialize KiteConnect
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info("Successfully connected to Kite API.")
    except Exception as e:
        logging.error(f"Authentication failed: {e}")
        sys.exit(1)

    logging.info(f"Looking for {instrument_name} {strike_price} {option_type}...")

    # Find the instrument token for the specified option
    instrument_token = None
    try:
        instruments = kite.instruments("NFO")
        for instrument in instruments:
            if (instrument['name'] == instrument_name and
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

                # Alert
                # We check if the price is within 0.5 of the alert price
                if (alert_price - 0.5) <= ltp <= (alert_price + 0.5) and not alert_triggered:
                    logging.info(f"Price is around {alert_price}! Playing alert.")
                    play_alert()
                    alert_triggered = True

                # Entry
                if ltp >= entry_price_target and entry_price is None:
                    entry_price = entry_price_target
                    logging.info(f"--- ENTRY TRIGGERED at {entry_price} ---")

                # Stop-loss and Target
                if entry_price is not None:
                    # Stop-loss
                    if ltp <= stop_loss_price:
                        logging.warning(f"--- STOP-LOSS HIT at {ltp} ---")
                        ws.close()
                    # Target
                    elif ltp >= target_price:
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
