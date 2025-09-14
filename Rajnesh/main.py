import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
from trading_logic import (
    initialize_kite,
    get_niftybank_index_token,
    get_first_5min_candle,
    check_candle_size,
    get_atm_strike_price,
    check_breakout,
    get_atm_option_contracts,
    place_order,
)
import datetime as dt
from config_editor import ConfigEditor
from ui import MainUI
from trade_logger import log_trade
from datetime import datetime

class TradingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nifty Bank Options Trading")
        self.geometry("400x300")

        self.config = self.load_config()

        # Application state variables
        self.kite = None
        self.instrument_token = None
        self.first_candle = None
        self.active_trade = None

        # Create UI variables
        self.sl_var = tk.StringVar(value=self.config.get('DEFAULT', 'SL', fallback='20'))
        self.target_var = tk.StringVar(value=self.config.get('DEFAULT', 'TARGET', fallback='50'))
        self.quantity_var = tk.StringVar(value="1")
        self.atm_strike_var = tk.StringVar(value="N/A")
        self.status_var = tk.StringVar(value="Ready")

        # Create the UI
        self.ui = MainUI(self, self.get_callbacks(), self.get_app_vars())

    def get_callbacks(self):
        return {
            'open_config_editor': self.open_config_editor,
            'start_trading': self.start_trading,
            'stop_trading': self.stop_trading,
            'set_buttons': self.set_buttons
        }

    def get_app_vars(self):
        return {
            'sl_var': self.sl_var,
            'target_var': self.target_var,
            'quantity_var': self.quantity_var,
            'atm_strike_var': self.atm_strike_var,
            'status_var': self.status_var
        }

    def set_buttons(self, start_button, stop_button):
        self.start_button = start_button
        self.stop_button = stop_button

    def open_config_editor(self):
        config_editor = ConfigEditor(self)
        config_editor.grab_set()
        self.wait_window(config_editor)
        self.config = self.load_config()
        self.sl_var.set(self.config.get('DEFAULT', 'SL', fallback='20'))
        self.target_var.set(self.config.get('DEFAULT', 'TARGET', fallback='50'))

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        if os.path.exists(config_path):
            config.read(config_path)
        return config

    def start_trading(self):
        self.status_var.set("Initializing...")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        try:
            self.kite = initialize_kite()
            self.instrument_token = get_niftybank_index_token(self.kite)
            if not self.instrument_token:
                messagebox.showerror("Error", "Could not find instrument token for NIFTY BANK index.")
                self.stop_trading()
                return

            self.status_var.set("Fetching first 5min candle...")
            self.check_first_candle()
        except (FileNotFoundError, ValueError, Exception) as e:
            messagebox.showerror("Error", str(e))
            self.stop_trading()

    def check_first_candle(self):
        self.first_candle = get_first_5min_candle(self.kite, self.instrument_token)
        if not self.first_candle:
            self.status_var.set("Could not fetch first candle. Retrying in 1 min...")
            self.after(60000, self.check_first_candle)
            return

        if not check_candle_size(self.first_candle):
            self.status_var.set(f"Candle size not in range. Size: {self.first_candle['high'] - self.first_candle['low']:.2f}. No trade.")
            self.stop_trading()
            return

        self.status_var.set(f"Candle OK. High: {self.first_candle['high']}, Low: {self.first_candle['low']}. Waiting for breakout.")
        self.monitor_breakout()

    def monitor_breakout(self):
        if self.active_trade: return
        try:
            ltp_data = self.kite.ltp([self.instrument_token])
            ltp = ltp_data[str(self.instrument_token)]['last_price']
            self.atm_strike_var.set(str(get_atm_strike_price(ltp)))
            breakout = check_breakout(ltp, self.first_candle)
            if breakout:
                self.handle_breakout(breakout)
            else:
                self.status_var.set(f"Monitoring for breakout... LTP: {ltp}")
                self.after(5000, self.monitor_breakout)
        except Exception as e:
            self.status_var.set(f"Error fetching LTP: {e}")
            self.after(5000, self.monitor_breakout)

    def handle_breakout(self, direction):
        self.status_var.set(f"Breakout detected ({direction})! Placing trade...")
        try:
            sl_points = int(self.sl_var.get())
            target_points = int(self.target_var.get())
            quantity_lots = int(self.quantity_var.get())

            ltp_data = self.kite.ltp([self.instrument_token])
            ltp = ltp_data[str(self.instrument_token)]['last_price']
            atm_strike = get_atm_strike_price(ltp)
            contracts = get_atm_option_contracts(self.kite, atm_strike)

            if not contracts or not contracts['ce'] or not contracts['pe']:
                messagebox.showerror("Error", "Could not fetch ATM option contracts.")
                self.stop_trading()
                return

            if direction == 'high':
                trade_instrument = contracts['ce']
                sl_price = self.first_candle['high'] - sl_points
                target_price = self.first_candle['high'] + target_points
                transaction_type = "BUY CE"
            else:
                trade_instrument = contracts['pe']
                sl_price = self.first_candle['low'] + sl_points
                target_price = self.first_candle['low'] - target_points
                transaction_type = "BUY PE"

            # Get the entry price of the option
            option_ltp_data = self.kite.ltp([trade_instrument['instrument_token']])
            entry_price = option_ltp_data[str(trade_instrument['instrument_token'])]['last_price']

            order_id = place_order(self.kite, trade_instrument['tradingsymbol'], trade_instrument['exchange'], 'BUY', quantity_lots * 15)
            if order_id:
                self.active_trade = {
                    'instrument': trade_instrument,
                    'transaction_type': transaction_type,
                    'quantity': quantity_lots * 15,
                    'entry_price': entry_price,
                    'entry_time': datetime.now().strftime('%H:%M:%S'),
                    'sl_price_index': sl_price,
                    'target_price_index': target_price,
                    'order_id': order_id
                }
                self.status_var.set(f"Trade placed for {trade_instrument['tradingsymbol']}. Monitoring SL/Target.")
                self.monitor_trade()
            else:
                messagebox.showerror("Error", "Failed to place order.")
                self.stop_trading()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during trade execution: {e}")
            self.stop_trading()

    def monitor_trade(self):
        if not self.active_trade: return
        try:
            index_ltp_data = self.kite.ltp([self.instrument_token])
            index_ltp = index_ltp_data[str(self.instrument_token)]['last_price']

            self.status_var.set(f"Monitoring trade... Index LTP: {index_ltp}, SL: {self.active_trade['sl_price_index']}, Target: {self.active_trade['target_price_index']}")

            exit_trade = False
            trade_instrument_type = self.active_trade['instrument']['instrument_type']
            if trade_instrument_type == 'CE':
                if index_ltp <= self.active_trade['sl_price_index'] or index_ltp >= self.active_trade['target_price_index']: exit_trade = True
            elif trade_instrument_type == 'PE':
                if index_ltp >= self.active_trade['sl_price_index'] or index_ltp <= self.active_trade['target_price_index']: exit_trade = True

            if exit_trade:
                self.status_var.set("SL/Target hit! Exiting trade.")
                # Get option exit price for logging
                option_ltp_data = self.kite.ltp([self.active_trade['instrument']['instrument_token']])
                exit_price = option_ltp_data[str(self.active_trade['instrument']['instrument_token'])]['last_price']

                # Place exit order
                place_order(self.kite, self.active_trade['instrument']['tradingsymbol'], self.active_trade['instrument']['exchange'], 'SELL', self.active_trade['quantity'])

                # Log the trade
                pnl = (exit_price - self.active_trade['entry_price']) * self.active_trade['quantity']
                trade_details = {
                    'instrument': self.active_trade['instrument']['tradingsymbol'],
                    'transaction_type': self.active_trade['transaction_type'],
                    'quantity': self.active_trade['quantity'],
                    'entry_time': self.active_trade['entry_time'],
                    'entry_price': self.active_trade['entry_price'],
                    'exit_time': datetime.now().strftime('%H:%M:%S'),
                    'exit_price': exit_price,
                    'pnl': pnl
                }
                log_trade(trade_details)

                self.stop_trading()
            else:
                self.after(5000, self.monitor_trade)
        except Exception as e:
            self.status_var.set(f"Error monitoring trade: {e}")
            self.after(5000, self.monitor_trade)

    def stop_trading(self):
        self.active_trade = None
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Stopped")

if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()
