import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import logging
from api_client import KrakenAPIClient
from models.portfolio import Portfolio
from models.favorites import Favorites
from utils import TextWidgetHandler
import csv

class KrakenBotGUI:
    def __init__(self, root, api_key: str, api_secret: str):
        """
        Initialisiert die GUI mit den angegebenen API-Schlüsseln.

        :param root: Das Hauptfenster der Anwendung.
        :param api_key: Der API-Schlüssel für die Kraken API.
        :param api_secret: Das API-Geheimnis für die Kraken API.
        """
        self.root = root
        self.root.title("Kraken Bot")
        self.dark_mode = False
        self.update_interval = 60000  # Default: 60 seconds
        self.trading_fee = 0.0026  # Default trading fee: 0.26%

        # Initialize API client with provided credentials
        self.api_client = KrakenAPIClient(api_key, api_secret)

        # Initialize portfolio and favorites
        self.portfolio = Portfolio(portfolio_file="portfolio.json")
        self.favorites = Favorites(favorites_file="favorites.json")

        # Create menu bar
        self.create_menu_bar()

        # Main frame
        self.frame = ttk.Frame(root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Balance label
        self.balance_label = ttk.Label(self.frame, text="Balance:")
        self.balance_label.grid(row=0, column=0, sticky=tk.W)

        # Treeview for portfolio
        self.tree = ttk.Treeview(self.frame, columns=("pair", "available", "market_price", "buy_price", "current_value", "deviation"), show='headings')
        self.tree.heading("pair", text="Pair")
        self.tree.heading("available", text="Available")
        self.tree.heading("market_price", text="Market Price (EUR)")
        self.tree.heading("buy_price", text="Buy Price (EUR)")
        self.tree.heading("current_value", text="Current Value (EUR)")
        self.tree.heading("deviation", text="Deviation (%)")
        self.tree.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll_y.grid(row=1, column=3, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set)

        self.tree_scroll_x = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree_scroll_x.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=self.tree_scroll_x.set)

        # Buttons
        self.update_button = ttk.Button(self.frame, text="Refresh", command=self.update_balance)
        self.update_button.grid(row=3, column=0, sticky=tk.W)

        self.export_button = ttk.Button(self.frame, text="Export Portfolio", command=self.export_portfolio)
        self.export_button.grid(row=3, column=1, sticky=tk.W)

        self.favorites_button = ttk.Button(self.frame, text="Manage Favorites", command=self.open_favorites_window)
        self.favorites_button.grid(row=3, column=2, sticky=tk.W)

        self.trade_button = ttk.Button(self.frame, text="Execute Trade", command=self.open_trade_window)
        self.trade_button.grid(row=3, column=3, sticky=tk.E)

        self.quit_button = ttk.Button(self.frame, text="Quit", command=root.quit)
        self.quit_button.grid(row=4, column=3, sticky=tk.E)

        # Console output
        self.console_output = tk.Text(self.frame, height=10, wrap=tk.WORD)
        self.console_output.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add custom logging handler for GUI
        text_handler = TextWidgetHandler(self.console_output)
        text_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(text_handler)

        # Start auto-update
        self.update_balance()
        self.auto_update()

    def create_menu_bar(self):
        """
        Erstellt die Menüleiste der Anwendung.
        """
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Update API Credentials", command=self.update_api_credentials)
        settings_menu.add_command(label="Set Update Interval", command=self.set_update_interval)
        settings_menu.add_command(label="Set Trading Fee", command=self.set_trading_fee)
        settings_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # Favorites menu
        favorites_menu = tk.Menu(menu_bar, tearoff=0)
        favorites_menu.add_command(label="Import Favorites", command=self.import_favorites)
        favorites_menu.add_command(label="Export Favorites", command=self.export_favorites)
        menu_bar.add_cascade(label="Favorites", menu=favorites_menu)

    def update_api_credentials(self):
        """
        Aktualisiert die API-Schlüssel.
        """
        api_key = simpledialog.askstring("Update API Key", "Enter new API Key:")
        api_secret = simpledialog.askstring("Update API Secret", "Enter new API Secret:")
        if api_key and api_secret:
            self.api_client = KrakenAPIClient(api_key, api_secret)
            logging.info("API credentials updated.")

    def set_update_interval(self):
        """
        Setzt das Aktualisierungsintervall.
        """
        interval = simpledialog.askinteger("Set Update Interval", "Enter update interval (in seconds):", minvalue=10)
        if interval:
            self.update_interval = interval * 1000
            logging.info(f"Update interval set to {interval} seconds.")

    def set_trading_fee(self):
        """
        Setzt die Handelsgebühr.
        """
        fee = simpledialog.askfloat("Set Trading Fee", "Enter trading fee (e.g., 0.0026 for 0.26%):", minvalue=0)
        if fee is not None:
            self.trading_fee = fee
            logging.info(f"Trading fee set to {fee * 100}%.")

    def toggle_dark_mode(self):
        """
        Schaltet den Dark Mode ein oder aus.
        """
        self.dark_mode = not self.dark_mode
        bg_color = "#2E2E2E" if self.dark_mode else "white"
        fg_color = "white" if self.dark_mode else "black"
        self.root.configure(bg=bg_color)
        self.console_output.configure(bg=bg_color, fg=fg_color)
        logging.info(f"Dark mode {'enabled' if self.dark_mode else 'disabled'}.")

    def update_balance(self):
        """
        Aktualisiert den Kontostand und zeigt ihn in der Tabelle an.
        """
        favorites = self.favorites.get_favorites()
        balance = self.api_client.check_balance(favorites)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for base_currency, available in balance.items():
            pair = f"{base_currency}EUR"
            if pair in favorites and available > 0:
                market_price = self.api_client.get_market_price(pair)
                buy_price = self.api_client.get_buy_price(pair)
                current_value = round(market_price * available, 2) if market_price else "N/A"
                deviation = ((market_price - buy_price) / buy_price) * 100 if market_price and buy_price else "N/A"
                self.tree.insert("", "end", values=(pair, available, market_price, buy_price, current_value, deviation))

    def auto_update(self):
        """
        Automatische Aktualisierung des Kontostands.
        """
        self.update_balance()
        self.root.after(self.update_interval, self.auto_update)

    def export_portfolio(self):
        """
        Exportiert das Portfolio in eine CSV-Datei.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Pair", "Available", "Market Price (EUR)", "Buy Price (EUR)", "Current Value (EUR)", "Deviation (%)"])
                for row_id in self.tree.get_children():
                    row = self.tree.item(row_id)['values']
                    writer.writerow(row)
            logging.info("Portfolio exported to CSV.")

    def open_favorites_window(self):
        """
        Öffnet ein Fenster zur Verwaltung der Favoriten.
        """
        favorites_window = tk.Toplevel(self.root)
        favorites_window.title("Manage Favorites")

        frame = ttk.Frame(favorites_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        favorites_label = ttk.Label(frame, text="Favorites:")
        favorites_label.grid(row=0, column=0, sticky=tk.W)

        self.favorites_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE)
        self.favorites_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        favorites = self.favorites.get_favorites()
        for favorite in favorites:
            self.favorites_listbox.insert(tk.END, favorite)

        add_button = ttk.Button(frame, text="Add", command=self.add_favorite)
        add_button.grid(row=2, column=0, sticky=tk.W)

        remove_button = ttk.Button(frame, text="Remove", command=self.remove_favorite)
        remove_button.grid(row=2, column=1, sticky=tk.E)

    def add_favorite(self):
        """
        Fügt ein neues Favoriten-Paar hinzu.
        """
        new_favorite = simpledialog.askstring("Add Favorite", "Enter the new favorite pair:")
        if new_favorite:
            self.favorites_listbox.insert(tk.END, new_favorite)
            favorites = list(self.favorites_listbox.get(0, tk.END))
            self.favorites.favorites = favorites  # Aktualisiere die Favoritenliste
            self.favorites.save_favorites()  # Speichere die aktualisierte Liste

    def remove_favorite(self):
        """
        Entfernt ein Favoriten-Paar.
        """
        selected_indices = self.favorites_listbox.curselection()
        for index in selected_indices[::-1]:
            self.favorites_listbox.delete(index)
        favorites = list(self.favorites_listbox.get(0, tk.END))
        self.favorites.favorites = favorites  # Aktualisiere die Favoritenliste
        self.favorites.save_favorites()  # Speichere die aktualisierte Liste

    def open_trade_window(self):
        """
        Öffnet ein Fenster zur Ausführung eines Trades.
        """
        trade_window = tk.Toplevel(self.root)
        trade_window.title("Execute Trade")

        frame = ttk.Frame(trade_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Pair:").grid(row=0, column=0, sticky=tk.W)
        pair_entry = ttk.Entry(frame, width=20)
        pair_entry.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(frame, text="Volume:").grid(row=1, column=0, sticky=tk.W)
        volume_entry = ttk.Entry(frame, width=20)
        volume_entry.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Side (buy/sell):").grid(row=2, column=0, sticky=tk.W)
        side_entry = ttk.Entry(frame, width=20)
        side_entry.grid(row=2, column=1, sticky=tk.W)

        execute_button = ttk.Button(frame, text="Execute", command=lambda: self.execute_trade(pair_entry.get(), volume_entry.get(), side_entry.get()))
        execute_button.grid(row=3, column=0, columnspan=2, pady=10)

    def execute_trade(self, pair, volume, side):
        """
        Führt einen Trade aus.
        """
        try:
            volume_float = float(volume)
            if side.lower() not in ['buy', 'sell']:
                messagebox.showerror("Error", "Side must be 'buy' or 'sell'.")
                return
            result = self.api_client.execute_trade(pair, volume_float, side.lower())
            if result:
                messagebox.showinfo("Success", f"Trade executed: {result}")
            else:
                messagebox.showerror("Error", "Failed to execute trade.")
        except ValueError:
            messagebox.showerror("Error", "Volume must be a number.")

    def import_favorites(self):
        """
        Importiert Favoriten aus einer JSON-Datei.
        """
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    favorites = json.load(f)
                    self.favorites.favorites = favorites  # Aktualisiere die Favoritenliste
                    self.favorites.save_favorites()  # Speichere die aktualisierte Liste
                    logging.info(f"Favorites imported from {file_path}")
                    messagebox.showinfo("Success", "Favorites imported successfully.")
            except Exception as e:
                logging.error(f"Error importing favorites: {e}")
                messagebox.showerror("Error", f"Failed to import favorites: {e}")

    def export_favorites(self):
        """
        Exportiert Favoriten in eine JSON-Datei.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                favorites = self.favorites.get_favorites()
                with open(file_path, 'w') as f:
                    json.dump(favorites, f, indent=4)
                logging.info(f"Favorites exported to {file_path}")
                messagebox.showinfo("Success", "Favorites exported successfully.")
            except Exception as e:
                logging.error(f"Error exporting favorites: {e}")
                messagebox.showerror("Error", f"Failed to export favorites: {e}")