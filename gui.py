import tkinter as tk
from tkinter import ttk
import configparser
import subprocess
import threading
import sys

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Trading Bot Control Panel")
        self.geometry("800x600")

        # Create the main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the Tabbed Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Create Tabs ---
        self.live_tab = ttk.Frame(self.notebook)
        self.backtest_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.live_tab, text="Live Trading")
        self.notebook.add(self.backtest_tab, text="Backtesting")

        # --- Populate Tabs ---
        self.create_live_tab_widgets()
        self.create_backtest_tab_widgets()

        # --- Console Output ---
        console_frame = ttk.LabelFrame(main_frame, text="Logs")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.console = tk.Text(console_frame, wrap=tk.WORD, height=10)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set, state=tk.DISABLED)

    def create_live_tab_widgets(self):
        # This dictionary will hold the Entry widgets to easily access their content
        self.live_widgets = {}

        config = configparser.ConfigParser()
        # Fallback to an empty config if file doesn't exist
        if not config.read('config_live.ini'):
            config.add_section('KITE')
            config.add_section('TRADING')

        # --- KITE Section ---
        kite_frame = ttk.LabelFrame(self.live_tab, text="KITE Credentials")
        kite_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.live_widgets['KITE'] = self.create_section_widgets(kite_frame, config, 'KITE')

        # --- TRADING Section ---
        trading_frame = ttk.LabelFrame(self.live_tab, text="TRADING Parameters")
        trading_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.live_widgets['TRADING'] = self.create_section_widgets(trading_frame, config, 'TRADING')

        # --- Action Buttons ---
        button_frame = ttk.Frame(self.live_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10, anchor='n')

        save_button = ttk.Button(button_frame, text="Save Live Config", command=self.save_live_config)
        save_button.pack(side=tk.LEFT, padx=5)

        self.run_live_button = ttk.Button(button_frame, text="Run Live Bot", command=lambda: self.start_script_thread('trading_bot.py'))
        self.run_live_button.pack(side=tk.LEFT, padx=5)

    def create_section_widgets(self, parent, config, section_name):
        widgets = {}
        if section_name in config:
            for key, value in config.items(section_name):
                row_frame = ttk.Frame(parent)
                row_frame.pack(fill=tk.X, padx=5, pady=2, anchor='n')

                label = ttk.Label(row_frame, text=f"{key.replace('_', ' ').title()}:", width=20)
                label.pack(side=tk.LEFT)

                entry = ttk.Entry(row_frame)
                entry.insert(0, value)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                widgets[key] = entry
        return widgets

    def save_live_config(self):
        config = configparser.ConfigParser()
        # Read existing structure if available
        config.read('config_live.ini')

        for section, widgets in self.live_widgets.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, widget in widgets.items():
                config.set(section, key, widget.get())

        try:
            with open('config_live.ini', 'w') as configfile:
                config.write(configfile)
            self.log_to_console("Live config saved successfully.\n")
        except Exception as e:
            self.log_to_console(f"Error saving config_live.ini: {e}\n")

    def create_backtest_tab_widgets(self):
        self.backtest_widgets = {}
        config = configparser.ConfigParser()
        if not config.read('config_backtest.ini'):
            config.add_section('KITE')
            config.add_section('TRADING')
            config.add_section('BACKTEST')

        # --- KITE Section ---
        kite_frame = ttk.LabelFrame(self.backtest_tab, text="KITE Credentials")
        kite_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.backtest_widgets['KITE'] = self.create_section_widgets(kite_frame, config, 'KITE')

        # --- TRADING Section ---
        trading_frame = ttk.LabelFrame(self.backtest_tab, text="TRADING Parameters")
        trading_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.backtest_widgets['TRADING'] = self.create_section_widgets(trading_frame, config, 'TRADING')

        # --- BACKTEST Section ---
        backtest_frame = ttk.LabelFrame(self.backtest_tab, text="BACKTEST Parameters")
        backtest_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.backtest_widgets['BACKTEST'] = self.create_section_widgets(backtest_frame, config, 'BACKTEST')

        # --- Action Buttons ---
        button_frame = ttk.Frame(self.backtest_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10, anchor='n')

        save_button = ttk.Button(button_frame, text="Save Backtest Config", command=self.save_backtest_config)
        save_button.pack(side=tk.LEFT, padx=5)

        self.run_backtest_button = ttk.Button(button_frame, text="Run Backtester", command=lambda: self.start_script_thread('backtester.py'))
        self.run_backtest_button.pack(side=tk.LEFT, padx=5)

    def save_backtest_config(self):
        config = configparser.ConfigParser()
        config.read('config_backtest.ini')

        for section, widgets in self.backtest_widgets.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, widget in widgets.items():
                config.set(section, key, widget.get())

        try:
            with open('config_backtest.ini', 'w') as configfile:
                config.write(configfile)
            self.log_to_console("Backtest config saved successfully.\n")
        except Exception as e:
            self.log_to_console(f"Error saving config_backtest.ini: {e}\n")

    def log_to_console(self, message):
        def append():
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, message)
            self.console.see(tk.END) # Auto-scroll
            self.console.config(state=tk.DISABLED)
        # Schedule the GUI update to run in the main thread
        self.after(0, append)


    def start_script_thread(self, script_name):
        # Disable buttons to prevent multiple runs
        self.run_live_button.config(state=tk.DISABLED)
        self.run_backtest_button.config(state=tk.DISABLED)

        # Clear the console before a new run
        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_script, args=(script_name,))
        thread.daemon = True
        thread.start()

    def run_script(self, script_name):
        try:
            # Using -u for unbuffered output is crucial for live logs
            self.log_to_console(f"--- Running {script_name} ---\n")
            process = subprocess.Popen(
                ['python', '-u', script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log_to_console(output)

            process.wait() # Wait for the process to finish
            self.log_to_console(f"\n--- {script_name} finished ---\n")

        except Exception as e:
            self.log_to_console(f"Failed to run script '{script_name}': {e}\n")
        finally:
            # Re-enable buttons once the script is done
            self.run_live_button.config(state=tk.NORMAL)
            self.run_backtest_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = App()
    app.mainloop()
