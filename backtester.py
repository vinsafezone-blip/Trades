import logging
import configparser
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import sys

def main():
    """
    Main function to run the backtester.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("--- Starting Backtester ---")

    # 1. Read Configuration
    config = configparser.ConfigParser()
    try:
        if not config.read('config.ini'):
            logging.error("Could not read config.ini. Please make sure the file exists.")
            sys.exit(1)

        # KITE credentials
        api_key = config.get('KITE', 'api_key')
        access_token = config.get('KITE', 'access_token')

        # TRADING parameters
        instrument_name = config.get('TRADING', 'instrument_name')
        strike_price = config.getint('TRADING', 'strike_price')
        option_type = config.get('TRADING', 'option_type').upper()
        entry_price_target = config.getfloat('TRADING', 'entry_price')
        stop_loss_price = config.getfloat('TRADING', 'stop_loss_price')
        target_price = config.getfloat('TRADING', 'target_price')

        # BACKTEST parameters
        from_date_str = config.get('BACKTEST', 'from_date')
        to_date_str = config.get('BACKTEST', 'to_date')
        interval = config.get('BACKTEST', 'interval')
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

    except (KeyError, configparser.NoSectionError, ValueError) as e:
        logging.error(f"Error reading config.ini: {e}. Make sure all sections and keys are correctly set up.")
        sys.exit(1)

    # 2. Initialize KiteConnect
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info("Successfully connected to Kite API.")
    except Exception as e:
        logging.error(f"Authentication failed: {e}")
        sys.exit(1)

    # 3. Find the correct instrument for the backtest period
    instrument_token = None
    try:
        instruments = kite.instruments("NFO")

        # Filter instruments to find potential matches
        potential_instruments = []
        for instrument in instruments:
            if (instrument['name'] == instrument_name and
                instrument['strike'] == strike_price and
                instrument['instrument_type'] == option_type and
                instrument['expiry'] > from_date.date()):
                potential_instruments.append(instrument)

        if not potential_instruments:
            raise ValueError("No matching option contracts found for the backtest period.")

        # Find the one with the nearest expiry date after the from_date
        potential_instruments.sort(key=lambda x: x['expiry'])
        target_instrument = potential_instruments[0]
        instrument_token = target_instrument['instrument_token']
        logging.info(f"Found instrument for backtest: {target_instrument['tradingsymbol']}")

    except Exception as e:
        logging.error(f"Error finding instrument: {e}")
        sys.exit(1)

    # 4. Fetch Historical Data
    try:
        logging.info(f"Fetching historical data for token {instrument_token} from {from_date_str} to {to_date_str}")
        records = kite.historical_data(instrument_token, from_date, to_date, interval)
        if not records:
            logging.warning("No historical data received for the specified period.")
            sys.exit(0)

        historical_df = pd.DataFrame(records)
        logging.info(f"Successfully fetched {len(historical_df)} records.")

    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        sys.exit(1)

    # 5. Run Backtesting Engine
    trades = []
    in_trade = False
    entry_price = 0
    trade_entry_time = None

    logging.info("Starting simulation...")
    for index, candle in historical_df.iterrows():
        high_price = candle['high']
        low_price = candle['low']

        # Entry logic
        if not in_trade:
            if high_price >= entry_price_target:
                in_trade = True
                entry_price = entry_price_target
                trade_entry_time = candle['date']
                logging.info(f"Trade Entry: Entered at {entry_price} on {trade_entry_time}")
                # In a real scenario, we might want to check if SL was also hit in the same candle
                # For this simulation, we assume entry is checked first.

        # Exit logic
        if in_trade:
            # Check for Stop-Loss
            if low_price <= stop_loss_price:
                profit = stop_loss_price - entry_price
                trades.append({
                    "entry_time": trade_entry_time,
                    "exit_time": candle['date'],
                    "entry_price": entry_price,
                    "exit_price": stop_loss_price,
                    "profit": profit,
                    "exit_reason": "STOP-LOSS"
                })
                in_trade = False
                logging.info(f"Trade Exit (SL): Exited at {stop_loss_price} on {candle['date']}. Profit: {profit:.2f}")

            # Check for Target
            elif high_price >= target_price:
                profit = target_price - entry_price
                trades.append({
                    "entry_time": trade_entry_time,
                    "exit_time": candle['date'],
                    "entry_price": entry_price,
                    "exit_price": target_price,
                    "profit": profit,
                    "exit_reason": "TARGET"
                })
                in_trade = False
                logging.info(f"Trade Exit (TGT): Exited at {target_price} on {candle['date']}. Profit: {profit:.2f}")

    logging.info("Simulation complete.")

    # 6. Generate Performance Report
    generate_report(trades, from_date_str, to_date_str)

    logging.info("--- Backtesting Complete ---")


def generate_report(trades, from_date, to_date):
    """
    Calculates and prints a performance report from a list of trades.
    """
    if not trades:
        logging.info("No trades were executed during the backtest period.")
        return

    total_trades = len(trades)
    winning_trades = [t for t in trades if t['profit'] > 0]
    losing_trades = [t for t in trades if t['profit'] <= 0]

    num_wins = len(winning_trades)
    num_losses = len(losing_trades)
    win_rate = (num_wins / total_trades) * 100 if total_trades > 0 else 0

    total_profit = sum(t['profit'] for t in trades)

    avg_win_profit = sum(t['profit'] for t in winning_trades) / num_wins if num_wins > 0 else 0
    avg_loss = abs(sum(t['profit'] for t in losing_trades) / num_losses) if num_losses > 0 else 0

    risk_reward_ratio = avg_win_profit / avg_loss if avg_loss > 0 else float('inf')

    print("\n--- Backtest Performance Report ---")
    print(f" Period: {from_date} to {to_date}")
    print("-----------------------------------")
    print(f" Total Trades:      {total_trades}")
    print(f" Winning Trades:    {num_wins}")
    print(f" Losing Trades:     {num_losses}")
    print(f" Win Rate:          {win_rate:.2f}%")
    print("-----------------------------------")
    print(f" Total P/L:         {total_profit:.2f}")
    print(f" Avg. Win Profit:   {avg_win_profit:.2f}")
    print(f" Avg. Loss:         {avg_loss:.2f}")
    print(f" Risk/Reward Ratio: {risk_reward_ratio:.2f}")
    print("-----------------------------------")


if __name__ == "__main__":
    main()
