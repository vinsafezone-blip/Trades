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

        # Main frame for the application
        main_frame = ttk.Frame(self.master)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Frame for trading parameters
        params_frame = ttk.LabelFrame(main_frame, text="Trading Parameters")
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
        live_data_frame = ttk.LabelFrame(main_frame, text="Live Data")
        live_data_frame.pack(padx=10, pady=10, fill="x")

        # ATM Strike Price
        ttk.Label(live_data_frame, text="ATM Strike Price:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(live_data_frame, textvariable=self.app_vars['atm_strike_var']).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(padx=10, pady=10, fill="x")

        self.start_button = ttk.Button(controls_frame, text="Start Trading", command=self.app_callbacks['start_trading'])
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(controls_frame, text="Stop Trading", command=self.app_callbacks['stop_trading'], state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Status Bar
        ttk.Label(self.master, textvariable=self.app_vars['status_var'], relief=tk.SUNKEN, anchor="w").pack(side=tk.BOTTOM, fill="x")

        # Share buttons with the app logic class
        self.app_callbacks['set_buttons'](self.start_button, self.stop_button)
