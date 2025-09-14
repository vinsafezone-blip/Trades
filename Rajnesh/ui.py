import tkinter as tk
from tkinter import ttk

class MainUI:
    def __init__(self, master, app_callbacks, app_vars):
        self.master = master
        self.app_callbacks = app_callbacks
        self.app_vars = app_vars

        self.create_widgets()

    def create_widgets(self):
        # Top frame for settings button
        top_frame = ttk.Frame(self.master)
        top_frame.pack(fill="x", padx=10, pady=5)

        settings_button = ttk.Button(top_frame, text="Settings", command=self.app_callbacks['open_config_editor'])
        settings_button.pack(side="right")

        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(self.master)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Create frames for each tab
        live_trade_frame = ttk.Frame(notebook)
        backtest_frame = ttk.Frame(notebook)

        notebook.add(live_trade_frame, text="Live Trading")
        notebook.add(backtest_frame, text="Backtesting")

        # Populate the live trading tab
        self.create_live_trade_widgets(live_trade_frame)

        # Populate the backtesting tab
        self.create_backtest_widgets(backtest_frame)

    def create_live_trade_widgets(self, parent_frame):
        # Frame for trading parameters
        params_frame = ttk.LabelFrame(parent_frame, text="Trading Parameters")
        params_frame.pack(padx=10, pady=10, fill="x")

        # SL
        ttk.Label(params_frame, text="Stop Loss (points):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.app_vars['sl_var']).grid(row=0, column=1, padx=5, pady=5)

        # Target
        ttk.Label(params_frame, text="Target (points):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.app_vars['target_var']).grid(row=1, column=1, padx=5, pady=5)

        # Quantity
        ttk.Label(params_frame, text="Quantity (Lots):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.app_vars['quantity_var']).grid(row=2, column=1, padx=5, pady=5)

        # Frame for live data
        live_data_frame = ttk.LabelFrame(parent_frame, text="Live Data")
        live_data_frame.pack(padx=10, pady=10, fill="x")

        # ATM Strike Price
        ttk.Label(live_data_frame, text="ATM Strike Price:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(live_data_frame, textvariable=self.app_vars['atm_strike_var']).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Controls
        controls_frame = ttk.Frame(parent_frame)
        controls_frame.pack(padx=10, pady=10, fill="x")

        start_button = ttk.Button(controls_frame, text="Start Trading", command=self.app_callbacks['start_trading'])
        start_button.pack(side="left", padx=5)

        stop_button = ttk.Button(controls_frame, text="Stop Trading", command=self.app_callbacks['stop_trading'], state="disabled")
        stop_button.pack(side="left", padx=5)

        self.app_callbacks['set_buttons'](start_button, stop_button)

        # Status Bar
        ttk.Label(self.master, textvariable=self.app_vars['status_var'], relief=tk.SUNKEN, anchor="w").pack(side=tk.BOTTOM, fill="x")

    def create_backtest_widgets(self, parent_frame):
        # Frame for backtest parameters
        params_frame = ttk.LabelFrame(parent_frame, text="Backtest Parameters")
        params_frame.pack(padx=10, pady=10, fill="x")

        # Start Date
        ttk.Label(params_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.app_vars['start_date_var']).grid(row=0, column=1, padx=5, pady=5)

        # End Date
        ttk.Label(params_frame, text="End Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(params_frame, textvariable=self.app_vars['end_date_var']).grid(row=1, column=1, padx=5, pady=5)

        # Run Button
        run_button = ttk.Button(params_frame, text="Run Backtest", command=self.app_callbacks['run_backtest_gui'])
        run_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Frame for results
        results_frame = ttk.LabelFrame(parent_frame, text="Backtest Results")
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        summary_text = tk.Text(results_frame, height=5, width=60)
        summary_text.pack(pady=5)

        # Treeview for individual trades
        trades_tree = ttk.Treeview(results_frame, columns=("Date", "Type", "Entry", "Exit", "P&L"), show="headings")
        trades_tree.pack(fill="both", expand=True)
        for col in trades_tree["columns"]:
            trades_tree.heading(col, text=col)
            trades_tree.column(col, width=100)

        # Share widgets with the app logic class
        self.app_callbacks['set_backtest_widgets'](summary_text, trades_tree)
