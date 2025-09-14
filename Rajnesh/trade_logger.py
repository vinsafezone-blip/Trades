import csv
import os
from datetime import datetime

def log_trade(trade_data):
    """
    Logs the details of a completed trade to a CSV file.

    Args:
        trade_data (dict): A dictionary containing the trade details.
                           Expected keys: 'instrument', 'transaction_type',
                           'entry_time', 'exit_time', 'entry_price',
                           'exit_price', 'pnl', 'quantity'
    """
    file_path = 'trade_log.csv'
    file_exists = os.path.isfile(file_path)

    fieldnames = [
        'Date', 'Instrument', 'Transaction Type', 'Quantity',
        'Entry Time', 'Entry Price', 'Exit Time', 'Exit Price', 'PNL'
    ]

    row_to_write = {
        'Date': datetime.now().strftime('%Y-%m-%d'),
        'Instrument': trade_data.get('instrument'),
        'Transaction Type': trade_data.get('transaction_type'),
        'Quantity': trade_data.get('quantity'),
        'Entry Time': trade_data.get('entry_time'),
        'Entry Price': f"{trade_data.get('entry_price'):.2f}",
        'Exit Time': trade_data.get('exit_time'),
        'Exit Price': f"{trade_data.get('exit_price'):.2f}",
        'PNL': f"{trade_data.get('pnl'):.2f}"
    }

    try:
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_to_write)
        print(f"Successfully logged trade: {row_to_write}")
    except Exception as e:
        print(f"Error logging trade: {e}")
