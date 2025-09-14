import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class ConfigEditor(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configuration Editor")
        self.geometry("400x250")

        self.config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.entries = {}
        settings = {
            "KITE": ["API_KEY", "API_SECRET"],
            "DEFAULT": ["SL", "TARGET", "SOUND_FILE"]
        }

        row = 0
        for section, keys in settings.items():
            ttk.Label(main_frame, text=section, font=("Helvetica", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=(10, 2), sticky="w")
            row += 1
            for key in keys:
                ttk.Label(main_frame, text=f"{key}:").grid(row=row, column=0, padx=5, pady=2, sticky="w")
                self.entries[f"{section}_{key}"] = ttk.Entry(main_frame, width=40)
                self.entries[f"{section}_{key}"].grid(row=row, column=1, padx=5, pady=2, sticky="ew")
                row += 1

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_button.pack(side="left", padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side="left", padx=5)

    def load_settings(self):
        for key, entry in self.entries.items():
            section, option = key.split('_')
            entry.insert(0, self.config.get(section, option, fallback=""))

    def save_settings(self):
        for key, entry in self.entries.items():
            section, option = key.split('_')
            self.config.set(section, option, entry.get())

        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

        messagebox.showinfo("Success", "Configuration saved successfully.")
        self.destroy()
