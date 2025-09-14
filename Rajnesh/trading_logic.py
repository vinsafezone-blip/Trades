# This file will contain the core trading logic.
import configparser
from kiteconnect import KiteConnect
import pandas as pd
import datetime as dt
import os

def initialize_kite():
    """Initializes and returns a KiteConnect object."""
    config = configparser.ConfigParser()
    # Assuming config.ini is in the same directory as this script
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    config.read(config_path)

    api_key = config['KITE']['API_KEY']
    api_secret = config['KITE']['API_SECRET']

    # The access_token needs to be obtained after a successful login flow.
    # For now, we will assume it is present in the config file.
    # In a real application, you would need to implement the login flow to get this.
    access_token = config['KITE'].get('ACCESS_TOKEN')

    if not all([api_key, api_secret, access_token]):
        raise ValueError("API_KEY, API_SECRET, or ACCESS_TOKEN is missing from config.ini")

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    return kite

def get_instrument_token(kite, exchange, tradingsymbol):
    """Gets the instrument token for a given trading symbol."""
    instruments = kite.instruments(exchange)
    df = pd.DataFrame(instruments)
    instrument = df.loc[df['tradingsymbol'] == tradingsymbol]
    if not instrument.empty:
        return instrument.iloc[0]['instrument_token']
    return None

def get_niftybank_index_token(kite):
    """Gets the instrument token for NIFTY BANK index."""
    return get_instrument_token(kite, "INDICES", "NIFTY BANK")

def get_atm_option_contracts(kite, atm_strike):
    """Gets the CE and PE contracts for the given ATM strike."""
    instruments = kite.instruments("NFO")
    df = pd.DataFrame(instruments)

    nifty_bank_options = df[(df['name'] == 'BANKNIFTY') & (df['instrument_type'] == 'CE') | (df['instrument_type'] == 'PE')]

    # Get the nearest expiry date
    nifty_bank_options['expiry'] = pd.to_datetime(nifty_bank_options['expiry'])
    nearest_expiry = nifty_bank_options['expiry'].min()

    atm_contracts = nifty_bank_options[(nifty_bank_options['strike'] == atm_strike) & (nifty_bank_options['expiry'] == nearest_expiry)]

    ce_contract = atm_contracts[atm_contracts['instrument_type'] == 'CE']
    pe_contract = atm_contracts[atm_contracts['instrument_type'] == 'PE']

    return {
        'ce': ce_contract.iloc[0].to_dict() if not ce_contract.empty else None,
        'pe': pe_contract.iloc[0].to_dict() if not pe_contract.empty else None,
    }

def get_first_5min_candle(kite, instrument_token):
    """
    Fetches the first 5-minute candle of the day for the given instrument.
    """
    today = dt.date.today()
    from_date = dt.datetime(today.year, today.month, today.day, 9, 15, 0)
    to_date = dt.datetime(today.year, today.month, today.day, 9, 20, 0)

    try:
        records = kite.historical_data(instrument_token, from_date, to_date, "5minute")
        if records:
            # The first record is the 5-minute candle
            return records[0]
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None
    return None


def check_candle_size(candle):
    """
    Checks if the candle size is within the specified range (130-300 points).
    'candle' is expected to be a dictionary with 'high' and 'low' keys.
    """
    if not candle:
        return False

    high = candle['high']
    low = candle['low']
    size = high - low

    if 130 <= size <= 300:
        return True
    return False


def get_atm_strike_price(price):
    """
    Determines the At-The-Money (ATM) strike price.
    For Nifty Bank, the strike price interval is 100 points.
    """
    return round(price / 100) * 100


def check_breakout(current_price, candle):
    """
    Checks if the current price has broken the high or low of the candle.
    'candle' is expected to be a dictionary with 'high' and 'low' keys.
    Returns 'high' if high is broken, 'low' if low is broken, else None.
    """
    if not candle:
        return None

    if current_price > candle['high']:
        return "high"
    elif current_price < candle['low']:
        return "low"
    return None
