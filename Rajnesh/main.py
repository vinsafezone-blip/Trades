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
)
from backtester import run_backtest
import datetime as dt
from pydub import AudioSegment
from pydub.playback import play
from config_editor import ConfigEditor

class TradingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nifty Bank Options Trading")
        self.geometry("600x400")

        self.config = self.load_config()
        self.create_widgets()
        self.kite = None
        self.instrument_token = None
        self.first_candle = None

    def open_config_editor(self):
        config_editor = ConfigEditor(self)
        config_editor.grab_set() # Make the window modal
        self.wait_window(config_editor) # Wait until the editor is closed
        self.config = self.load_config() # Reload the config
        self.sl_var.set(self.config.get('DEFAULT', 'SL', fallback='20'))
        self.target_var.set(self.config.get('DEFAULT', 'TARGET', fallback='50'))

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        if os.path.exists(config_path):
            config.read(config_path)
        return config

    def create_widgets(self):
        # Top frame for settings button
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)

        settings_button = ttk.Button(top_frame, text="Settings", command=self.open_config_editor)
        settings_button.pack(side="right")

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Create frames for each tab
        self.live_trade_frame = ttk.Frame(self.notebook)
        self.backtest_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.live_trade_frame, text="Live Trading")
        self.notebook.add(self.backtest_frame, text="Backtesting")

        # Populate the live trading tab
        self.create_live_trade_widgets()

        # Populate the backtesting tab
        self.create_backtest_widgets()

    def create_live_trade_widgets(self):
        # This method will contain the widgets for the live trading tab
        # Frame for trading parameters
        params_frame = ttk.LabelFrame(self.live_trade_frame, text="Trading Parameters")
        params_frame.pack(padx=10, pady=10, fill="x")

        # SL
        ttk.Label(params_frame, text="Stop Loss (points):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sl_var = tk.StringVar(value=self.config.get('DEFAULT', 'SL', fallback='20'))
        ttk.Entry(params_frame, textvariable=self.sl_var).grid(row=0, column=1, padx=5, pady=5)

        # Target
        ttk.Label(params_frame, text="Target (points):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.target_var = tk.StringVar(value=self.config.get('DEFAULT', 'TARGET', fallback='50'))
        ttk.Entry(params_frame, textvariable=self.target_var).grid(row=1, column=1, padx=5, pady=5)

        # Frame for live data
        live_data_frame = ttk.LabelFrame(self.live_trade_frame, text="Live Data")
        live_data_frame.pack(padx=10, pady=10, fill="x")

        # ATM Strike Price
        ttk.Label(live_data_frame, text="ATM Strike Price:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.atm_strike_var = tk.StringVar(value="N/A")
        ttk.Label(live_data_frame, textvariable=self.atm_strike_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Controls
        controls_frame = ttk.Frame(self.live_trade_frame)
        controls_frame.pack(padx=10, pady=10, fill="x")

        self.start_button = ttk.Button(controls_frame, text="Start Trading", command=self.start_trading)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(controls_frame, text="Stop Trading", command=self.stop_trading, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.live_trade_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w").pack(side=tk.BOTTOM, fill="x")

    def create_backtest_widgets(self):
        # This method will contain the widgets for the backtesting tab
        # Frame for backtest parameters
        params_frame = ttk.LabelFrame(self.backtest_frame, text="Backtest Parameters")
        params_frame.pack(padx=10, pady=10, fill="x")

        # Start Date
        ttk.Label(params_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.start_date_var = tk.StringVar(value=(dt.date.today() - dt.timedelta(days=30)).strftime('%Y-%m-%d'))
        ttk.Entry(params_frame, textvariable=self.start_date_var).grid(row=0, column=1, padx=5, pady=5)

        # End Date
        ttk.Label(params_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.end_date_var = tk.StringVar(value=dt.date.today().strftime('%Y-%m-%d'))
        ttk.Entry(params_frame, textvariable=self.end_date_var).grid(row=1, column=1, padx=5, pady=5)

        # Run Button
        run_button = ttk.Button(params_frame, text="Run Backtest", command=self.run_backtest_gui)
        run_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Frame for results
        results_frame = ttk.LabelFrame(self.backtest_frame, text="Backtest Results")
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.summary_text = tk.Text(results_frame, height=5, width=60)
        self.summary_text.pack(pady=5)

        # Treeview for individual trades
        self.trades_tree = ttk.Treeview(results_frame, columns=("Date", "Type", "Entry", "Exit", "P&L"), show="headings")
        self.trades_tree.pack(fill="both", expand=True)
        for col in self.trades_tree["columns"]:
            self.trades_tree.heading(col, text=col)
            self.trades_tree.column(col, width=100)

    def run_backtest_gui(self):
        self.summary_text.delete(1.0, tk.END)
        for i in self.trades_tree.get_children():
            self.trades_tree.delete(i)

        try:
            start_date_str = self.start_date_var.get()
            end_date_str = self.end_date_var.get()
            sl_points = int(self.sl_var.get())
            target_points = int(self.target_var.get())

            start_date = dt.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = dt.datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if not self.kite:
                self.kite = initialize_kite()

            if not self.instrument_token:
                self.instrument_token = get_niftybank_index_token(self.kite)

            if not self.instrument_token:
                messagebox.showerror("Error", "Could not find instrument token for NIFTY BANK index.")
                return

            summary, trades = run_backtest(self.kite, self.instrument_token, start_date, end_date, sl_points, target_points)

            if summary is None:
                messagebox.showinfo("Backtest", "No data found for the selected period.")
                return

            summary_str = (
                f"Total Trades: {summary['total_trades']}\n"
                f"Profitable Trades: {summary['profitable_trades']}\n"
                f"Loss-making Trades: {summary['loss_making_trades']}\n"
                f"Total P&L: {summary['total_pnl']:.2f}"
            )
            self.summary_text.insert(tk.END, summary_str)

            if trades:
                for trade in trades:
                    self.trades_tree.insert("", "end", values=(
                        trade['date'].strftime('%Y-%m-%d'),
                        trade['trade_type'],
                        f"{trade['entry_price']:.2f}",
                        f"{trade['exit_price']:.2f}",
                        f"{trade['pnl']:.2f}"
                    ))

        except (ValueError, TypeError) as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during backtesting: {e}")

    def start_trading(self):
        self.status_var.set("Initializing...")
        try:
            self.kite = initialize_kite()
            self.instrument_token = get_niftybank_index_token(self.kite)

            if not self.instrument_token:
                messagebox.showerror("Error", "Could not find instrument token for NIFTY BANK index.")
                self.status_var.set("Error: Instrument not found")
                return

            self.status_var.set("Fetching first 5min candle...")
            self.check_first_candle()

        except (FileNotFoundError, ValueError, Exception) as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error")

    def check_first_candle(self):
        self.first_candle = get_first_5min_candle(self.kite, self.instrument_token)

        if not self.first_candle:
            self.status_var.set("Could not fetch first candle. Retrying in 1 min...")
            self.after(60000, self.check_first_candle) # Retry after 1 minute
            return

        if not check_candle_size(self.first_candle):
            self.status_var.set("Candle size not in range (130-300). No trade.")
            self.stop_trading()
            return

        self.status_var.set(f"Candle OK. High: {self.first_candle['high']}, Low: {self.first_candle['low']}. Waiting for breakout.")

        self.monitor_breakout()

    def monitor_breakout(self):
        try:
            ltp_data = self.kite.ltp([self.instrument_token])
            ltp = ltp_data[str(self.instrument_token)]['last_price']
            atm_strike = get_atm_strike_price(ltp)
            self.atm_strike_var.set(str(atm_strike))

            breakout = check_breakout(ltp, self.first_candle)
            if breakout:
                self.handle_breakout(breakout)
            else:
                self.status_var.set(f"Monitoring for breakout... LTP: {ltp}")
                self.after(5000, self.monitor_breakout) # Check every 5 seconds

        except Exception as e:
            self.status_var.set(f"Error fetching LTP: {e}")
            self.after(5000, self.monitor_breakout)


    def play_alert_sound(self):
        sound_file_path = self.config.get('DEFAULT', 'SOUND_FILE', fallback=None)
        if sound_file_path and os.path.exists(sound_file_path):
            try:
                sound = AudioSegment.from_wav(sound_file_path)
                play(sound)
            except Exception as e:
                print(f"Could not play sound file: {e}")
        else:
            print("Sound file not found or not configured.")

    def handle_breakout(self, direction):
        self.status_var.set(f"Breakout detected ({direction})! Placing trade...")
        self.play_alert_sound()
        self.stop_trading()


    def stop_trading(self):
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Stopped")


if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()
