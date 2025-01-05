import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import logging
import sys
import pystray
from PIL import Image
from api_client import KrakenAPIClient
from models import *
from utils import TextWidgetHandler
import csv
from datetime import datetime
import time  # Importiere das time-Modul für Verzögerungen

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

        # Setze das Taskbar-Icon
        try:
            self.root.iconbitmap("icon.ico")  # Pfad zum Icon-Bild (ICO-Format)
        except Exception as e:
            logging.error(f"Fehler beim Laden des Taskbar-Icons: {e}")

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
        self.tree.heading("pair", text="Pair", command=lambda: self.sort_treeview(self.tree, "pair", False))
        self.tree.heading("available", text="Available", command=lambda: self.sort_treeview(self.tree, "available", False))
        self.tree.heading("market_price", text="Market Price (EUR)", command=lambda: self.sort_treeview(self.tree, "market_price", False))
        self.tree.heading("buy_price", text="Buy Price (EUR)", command=lambda: self.sort_treeview(self.tree, "buy_price", False))
        self.tree.heading("current_value", text="Current Value (EUR)", command=lambda: self.sort_treeview(self.tree, "current_value", False))
        self.tree.heading("deviation", text="Deviation (%)", command=lambda: self.sort_treeview(self.tree, "deviation", False))
        self.tree.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll_y.grid(row=1, column=3, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set)

        self.tree_scroll_x = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree_scroll_x.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.tree.configure(xscrollcommand=self.tree_scroll_x.set)

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

        # Tray Icon
        self.create_tray_icon()

        # Behandle das Schließen des Fensters
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Erstelle die Handelshistorie-Tab
        self.create_trades_tab()

        # Standard-Intervall für das Laden der Handelshistorie (5 Minuten)
        self.trades_history_interval = 300000  # 5 Minuten in Millisekunden

        # Starte das regelmäßige Laden der Handelshistorie
        self.auto_update_trades()

    def create_trades_tab(self):
        """
        Erstellt den Tab für die Handelshistorie mit einer Tabelle.
        """
        # Haupt-Tab-Control
        self.tab_control = ttk.Notebook(self.frame)
        self.tab_control.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tab für die Handelshistorie
        self.trades_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.trades_tab, text="Handelshistorie")

        # Tabelle für die Handelshistorie
        self.trades_tree = ttk.Treeview(
            self.trades_tab,
            columns=("pair", "type", "price", "volume", "time"),
            show="headings"
        )
        self.trades_tree.heading("pair", text="Paar")
        self.trades_tree.heading("type", text="Typ")
        self.trades_tree.heading("price", text="Preis")
        self.trades_tree.heading("volume", text="Volumen")
        self.trades_tree.heading("time", text="Zeit")
        self.trades_tree.pack(expand=True, fill="both")

        # Scrollbars für die Tabelle
        scroll_y = ttk.Scrollbar(self.trades_tab, orient="vertical", command=self.trades_tree.yview)
        scroll_y.pack(side="right", fill="y")
        self.trades_tree.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(self.trades_tab, orient="horizontal", command=self.trades_tree.xview)
        scroll_x.pack(side="bottom", fill="x")
        self.trades_tree.configure(xscrollcommand=scroll_x.set)

    def sort_treeview(self, tree, col, reverse):
        """
        Sortiert die Treeview nach der angegebenen Spalte.

        :param tree: Die Treeview-Komponente.
        :param col: Die Spalte, nach der sortiert werden soll.
        :param reverse: Gibt an, ob die Sortierung umgekehrt werden soll.
        """
        data = [(tree.set(item, col), item) for item in tree.get_children("")]
        data.sort(reverse=reverse)

        for index, (_, item) in enumerate(data):
            tree.move(item, "", index)

        # Setze den Sortierindikator in der Spaltenüberschrift
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))

    def fetch_and_display_trades(self):
        """
        Ruft die Handelshistorie ab und zeigt sie in einer Tabelle an.
        """
        try:
            logging.info("Lade Handelshistorie...")

            # Handelshistorie für alle Paare abrufen
            trades_history = None
            retries = 3  # Anzahl der Wiederholungsversuche
            delay = 15  # Verzögerung in Sekunden zwischen den Versuchen
            time.sleep(delay)  # Warte vor dem nächsten Versuch
            for attempt in range(retries):
                try:
                    trades_history = self.api_client.get_trades_history()
                    if trades_history:
                        break  # Erfolg, breche die Schleife ab
                    else:
                        logging.warning(f"Keine Handelshistorie gefunden. Versuch {attempt + 1} von {retries}.")
                except Exception as e:
                    if "EAPI:Rate limit exceeded" in str(e):
                        logging.warning(f"Rate-Limit überschritten. Versuch {attempt + 1} von {retries}. Warte {delay} Sekunden...")
                        time.sleep(delay)  # Warte vor dem nächsten Versuch
                    else:
                        logging.error(f"Fehler beim Abrufen der Handelshistorie: {e}")
                        raise e  # Wirf den Fehler erneut, wenn es sich nicht um einen Rate-Limit-Fehler handelt

            if not trades_history:
                logging.warning("Keine Handelshistorie gefunden.")
                return

            # Lösche alle vorhandenen Einträge in der Tabelle
            for row in self.trades_tree.get_children():
                self.trades_tree.delete(row)

            # Füge die Handelsdaten in die Tabelle ein
            for trade in trades_history:
                # Extrahiere die Handelsdaten
                pair = trade.get('pair', 'N/A')
                trade_type = trade.get('type', 'N/A')
                price = trade.get('price', 'N/A')
                volume = trade.get('vol', 'N/A')
                time_str = trade.get('time', 'N/A')

                # Konvertiere den Zeitstempel in das deutsche Datumsformat
                if time_str != 'N/A':
                    try:
                        time_str = datetime.fromtimestamp(float(time_str)).strftime("%d.%m.%Y %H:%M:%S")
                    except Exception as e:
                        logging.error(f"Fehler beim Konvertieren des Zeitstempels: {e}")
                        time_str = 'N/A'

                # Füge die Daten in die Tabelle ein
                self.trades_tree.insert("", "end", values=(pair, trade_type.upper(), price, volume, time_str))

            # Farbliche Hervorhebung basierend auf dem Handels-Typ (Buy/Sell)
            for row in self.trades_tree.get_children():
                trade_type = self.trades_tree.item(row, 'values')[1]
                if trade_type == 'BUY':
                    self.trades_tree.tag_configure("buy", background="lightgreen")
                    self.trades_tree.item(row, tags=("buy",))
                elif trade_type == 'SELL':
                    self.trades_tree.tag_configure("sell", background="lightcoral")
                    self.trades_tree.item(row, tags=("sell",))

            logging.info("Handelshistorie erfolgreich geladen und angezeigt.")

        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Handelshistorie: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden der Handelshistorie: {e}")

    def create_tooltip(self, widget, text):
        """
        Erstellt einen Tooltip für ein Widget.

        :param widget: Das Widget, für das der Tooltip erstellt wird.
        :param text: Der Text des Tooltips.
        """
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry("+0+0")
        tooltip.withdraw()

        label = ttk.Label(tooltip, text=text, background="lightyellow", padding=5)
        label.pack()

        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def create_tray_icon(self):
        """
        Erstellt ein Tray-Icon mit einem Menü.
        """
        # Bild für das Tray-Icon (verwendet das konvertierte PNG)
        try:
            image = Image.open("icon.png")  # Pfad zum Icon-Bild
        except FileNotFoundError:
            print("Icon-Bild nicht gefunden. Verwende Standard-Icon.")
            image = Image.new('RGB', (64, 64), color='gray')  # Fallback: einfaches graues Icon

        # Tray-Icon erstellen
        menu = pystray.Menu(
            pystray.MenuItem("Fenster wiederherstellen", self.restore_window),
            pystray.MenuItem("Beenden", self.quit_app)
        )
        self.icon = pystray.Icon("kraken_bot", image, "Kraken Bot", menu)

    def minimize_to_tray(self):
        """
        Minimiert das Fenster in das System-Tray.
        """
        self.root.withdraw()  # Fenster verstecken
        self.icon.run()  # Tray-Icon starten

    def restore_window(self, icon=None, item=None):
        """
        Stellt das Fenster aus dem System-Tray wieder her.
        """
        self.icon.stop()  # Tray-Icon beenden
        self.root.deiconify()  # Fenster wiederherstellen

    def quit_app(self, icon=None, item=None):
        """
        Beendet die Anwendung.
        """
        self.icon.stop()  # Tray-Icon beenden
        self.root.quit()  # Anwendung beenden

    def on_close(self):
        """
        Behandelt das Schließen des Fensters.
        """
        self.icon.stop()  # Tray-Icon beenden
        self.root.destroy()  # Fenster zerstören

    def create_menu_bar(self):
        """
        Erstellt die Menüleiste der Anwendung.
        """
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Refresh", command=self.update_balance)
        file_menu.add_command(label="Export Portfolio", command=self.export_portfolio)
        file_menu.add_command(label="In Tray minimieren", command=self.minimize_to_tray)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Favorites menu
        favorites_menu = tk.Menu(menu_bar, tearoff=0)
        favorites_menu.add_command(label="Manage Favorites", command=self.open_favorites_window)
        favorites_menu.add_command(label="Import Favorites", command=self.import_favorites)
        favorites_menu.add_command(label="Export Favorites", command=self.export_favorites)
        menu_bar.add_cascade(label="Favorites", menu=favorites_menu)

        # Trade menu
        trade_menu = tk.Menu(menu_bar, tearoff=0)
        trade_menu.add_command(label="Execute Trade", command=self.open_trade_window)
        menu_bar.add_cascade(label="Trade", menu=trade_menu)

        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Update API Credentials", command=self.update_api_credentials)
        settings_menu.add_command(label="Set Update Interval", command=self.set_update_interval)
        settings_menu.add_command(label="Set Trading Fee", command=self.set_trading_fee)
        settings_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        settings_menu.add_command(label="Set Trades History Interval", command=self.set_trades_history_interval)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # History menu
        history_menu = tk.Menu(menu_bar, tearoff=0)
        history_menu.add_command(label="Load Trade History", command=self.fetch_and_display_trades)
        menu_bar.add_cascade(label="History", menu=history_menu)

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
        Öffnet ein Fenster zum Setzen des Aktualisierungsintervalls.
        """
        interval_window = tk.Toplevel(self.root)
        interval_window.title("Set Update Interval")

        frame = ttk.Frame(interval_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Update Interval (in seconds):").grid(row=0, column=0, sticky=tk.W)

        # Dropdown-Menü für das Update-Intervall
        intervals = [10, 30, 60, 120, 300]  # Mögliche Intervalle in Sekunden
        self.interval_var = tk.StringVar(value=self.update_interval // 1000)  # Aktuelles Intervall
        interval_dropdown = ttk.Combobox(frame, textvariable=self.interval_var, values=intervals, state="readonly")
        interval_dropdown.grid(row=0, column=1, sticky=tk.W)

        # Button zum Bestätigen
        confirm_button = ttk.Button(frame, text="Confirm", command=lambda: self.confirm_update_interval(interval_window))
        confirm_button.grid(row=1, column=0, columnspan=2, pady=10)

    def confirm_update_interval(self, window):
        """
        Bestätigt das ausgewählte Update-Intervall.
        """
        try:
            interval = int(self.interval_var.get())
            if interval > 0:
                self.update_interval = interval * 1000
                logging.info(f"Update interval set to {interval} seconds.")
                window.destroy()
            else:
                messagebox.showerror("Error", "Interval must be greater than 0.")
        except ValueError:
            messagebox.showerror("Error", "Invalid interval value.")

    def set_trades_history_interval(self):
        """
        Öffnet ein Fenster zum Setzen des Intervalls für das Laden der Handelshistorie.
        """
        interval_window = tk.Toplevel(self.root)
        interval_window.title("Set Trades History Interval")

        frame = ttk.Frame(interval_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Interval (in minutes):").grid(row=0, column=0, sticky=tk.W)

        # Dropdown-Menü für das Intervall
        intervals = [1, 5, 10, 15, 30, 60]  # Mögliche Intervalle in Minuten
        self.trades_history_interval_var = tk.StringVar(value=self.trades_history_interval // 60000)  # Aktuelles Intervall
        interval_dropdown = ttk.Combobox(frame, textvariable=self.trades_history_interval_var, values=intervals, state="readonly")
        interval_dropdown.grid(row=0, column=1, sticky=tk.W)

        # Button zum Bestätigen
        confirm_button = ttk.Button(frame, text="Confirm", command=lambda: self.confirm_trades_history_interval(interval_window))
        confirm_button.grid(row=1, column=0, columnspan=2, pady=10)

    def confirm_trades_history_interval(self, window):
        """
        Bestätigt das ausgewählte Intervall für das Laden der Handelshistorie.
        """
        try:
            interval = int(self.trades_history_interval_var.get())
            if interval > 0:
                self.trades_history_interval = interval * 60000  # Konvertiere Minuten in Millisekunden
                logging.info(f"Trades history interval set to {interval} minutes.")
                window.destroy()
            else:
                messagebox.showerror("Error", "Interval must be greater than 0.")
        except ValueError:
            messagebox.showerror("Error", "Invalid interval value.")

    def set_trading_fee(self):
        """
        Setzt die Handelsgebühr.
        """
        fee_window = tk.Toplevel(self.root)
        fee_window.title("Set Trading Fee")

        frame = ttk.Frame(fee_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Trading Fee:").grid(row=0, column=0, sticky=tk.W)
        fee_var = tk.StringVar(value=str(self.trading_fee))  # Standardwert
        fee_dropdown = ttk.Combobox(frame, textvariable=fee_var, values=["0.001", "0.002", "0.0026", "0.005"], state="readonly")
        fee_dropdown.grid(row=0, column=1, sticky=tk.W)

        confirm_button = ttk.Button(frame, text="Confirm", command=lambda: self.confirm_trading_fee(fee_var.get(), fee_window))
        confirm_button.grid(row=1, column=0, columnspan=2, pady=10)

    def confirm_trading_fee(self, fee, window):
        """
        Bestätigt die ausgewählte Handelsgebühr.
        """
        try:
            fee_float = float(fee)
            if fee_float >= 0:
                self.trading_fee = fee_float
                logging.info(f"Trading fee set to {fee_float * 100}%.")
                window.destroy()
            else:
                messagebox.showerror("Error", "Fee must be greater than or equal to 0.")
        except ValueError:
            messagebox.showerror("Error", "Invalid fee value.")

    def toggle_dark_mode(self):
        """
        Schaltet den Dark Mode ein oder aus.
        """
        self.dark_mode = not self.dark_mode
        bg_color = "#2E2E2E" if self.dark_mode else "white"
        fg_color = "white" if self.dark_mode else "black"

        # Hauptfenster und Widgets
        self.root.configure(bg=bg_color)
        self.frame.configure(style="Dark.TFrame" if self.dark_mode else "TFrame")
        self.balance_label.configure(style="Dark.TLabel" if self.dark_mode else "TLabel")
        self.console_output.configure(bg=bg_color, fg=fg_color)

        # Treeview
        style = ttk.Style()
        style.configure("Dark.Treeview", background=bg_color, foreground=fg_color, fieldbackground=bg_color)
        style.configure("Dark.Treeview.Heading", background=bg_color, foreground=fg_color)
        self.tree.configure(style="Dark.Treeview" if self.dark_mode else "Treeview")

        logging.info(f"Dark mode {'enabled' if self.dark_mode else 'disabled'}.")

    def update_balance(self):
        """
        Aktualisiert den Kontostand und zeigt ihn in der Tabelle an.
        """
        try:
            favorites = self.favorites.get_favorites()
            balance = self.api_client.check_balance(favorites)

            # Überprüfe, ob sich der Kontostand geändert hat
            if hasattr(self, 'last_balance'):
                if self.last_balance != balance:
                    # Lade die Handelshistorie, wenn sich der Kontostand geändert hat
                    self.fetch_and_display_trades()
            self.last_balance = balance  # Speichere den aktuellen Kontostand

            # Lösche alle vorhandenen Einträge in der Tabelle
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Sammle die Daten in einer Liste
            data = []
            for base_currency, available in balance.items():
                pair = f"{base_currency}EUR"
                if pair in favorites and available > 0:
                    market_price = self.api_client.get_market_price(pair)
                    buy_price = self.api_client.get_buy_price(pair)
                    current_value = round(market_price * available, 2) if market_price else 0
                    deviation = ((market_price - buy_price) / buy_price) * 100 if market_price and buy_price else 0
                    data.append((pair, available, market_price, buy_price, current_value, deviation))

            # Sortiere die Daten nach dem aktuellen Wert absteigend
            data.sort(key=lambda x: x[4], reverse=True)

            # Füge die sortierten Daten in die Tabelle ein
            for row in data:
                self.tree.insert("", "end", values=row)

            # Speichere das Portfolio nach der Aktualisierung
            self.portfolio.portfolio = balance
            self.portfolio.save_portfolio()
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Balance: {e}")

    def auto_update(self):
        """
        Automatische Aktualisierung des Kontostands.
        """
        self.update_balance()
        self.root.after(self.update_interval, self.auto_update)

    def auto_update_trades(self):
        """
        Lädt die Handelshistorie in regelmäßigen Abständen.
        """
        self.fetch_and_display_trades()
        self.root.after(self.trades_history_interval, self.auto_update_trades)

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
        Öffnet ein Fenster zur Ausführung eines Trades mit Wallet-Auswahl und Favoriten-Dropdown.
        """
        trade_window = tk.Toplevel(self.root)
        trade_window.title("Execute Trade")

        frame = ttk.Frame(trade_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Dropdown für das Paar (aus den Favoriten)
        ttk.Label(frame, text="Pair:").grid(row=0, column=0, sticky=tk.W)
        pair_var = tk.StringVar()
        pair_dropdown = ttk.Combobox(frame, textvariable=pair_var, values=self.favorites.get_favorites(), state="readonly")
        pair_dropdown.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(frame, text="Volume:").grid(row=1, column=0, sticky=tk.W)
        volume_entry = ttk.Entry(frame, width=20)
        volume_entry.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Side (buy/sell):").grid(row=2, column=0, sticky=tk.W)
        side_var = tk.StringVar(value="buy")  # Standardwert
        side_dropdown = ttk.Combobox(frame, textvariable=side_var, values=["buy", "sell"], state="readonly")
        side_dropdown.grid(row=2, column=1, sticky=tk.W)

        ttk.Label(frame, text="Wallet Type:").grid(row=3, column=0, sticky=tk.W)
        wallet_type_var = tk.StringVar(value="spot")  # Standardwert
        wallet_type_dropdown = ttk.Combobox(frame, textvariable=wallet_type_var, values=["spot", "margin", "staking"], state="readonly")
        wallet_type_dropdown.grid(row=3, column=1, sticky=tk.W)

        execute_button = ttk.Button(frame, text="Execute", command=lambda: self.execute_trade(
            pair_var.get(),
            volume_entry.get(),
            side_var.get(),
            wallet_type_var.get()
        ))
        execute_button.grid(row=4, column=0, columnspan=2, pady=10)

    def execute_trade(self, pair, volume, side, wallet_type='spot'):
        """
        Führt einen Trade aus und wählt das Wallet (Spot, Margin oder Staking).

        :param pair: Das Handelspaar (z. B. 'ADAEUR').
        :param volume: Das Handelsvolumen.
        :param side: Die Handelsseite ('buy' oder 'sell').
        :param wallet_type: Der Wallet-Typ ('spot', 'margin' oder 'staking').
        """
        try:
            volume_float = float(volume)
            if side.lower() not in ['buy', 'sell']:
                messagebox.showerror("Error", "Side must be 'buy' or 'sell'.")
                return

            # Modaler Dialog zur Bestätigung des Trades
            confirm = messagebox.askyesno("Confirm Trade", f"Do you want to {side} {volume_float} of {pair} from {wallet_type} wallet?")
            if confirm:
                # Setze die Flags basierend auf dem Wallet-Typ
                if wallet_type == 'margin':
                    oflags = 'fcib,margin'  # Margin-Trading
                elif wallet_type == 'staking':
                    oflags = 'fcib,staking'  # Staking (falls unterstützt)
                else:
                    oflags = 'fcib'  # Spot-Trading

                # Verwende den api_client, um den Trade auszuführen
                result = self.api_client.execute_trade(pair, volume_float, side.lower(), oflags)
                logging.info(f"Trade execution response: {result}")
                if result:
                    messagebox.showinfo("Success", f"Trade executed: {result}")

                    # Aktualisiere die Balance und Handelshistorie nach dem Trade
                    self.update_balance()
                    self.fetch_and_display_trades()
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

if __name__ == "__main__":
    root = tk.Tk()
    api_key = "your_api_key_here"  # Ersetze dies durch deinen API-Schlüssel
    api_secret = "your_api_secret_here"  # Ersetze dies durch dein API-Geheimnis
    app = KrakenBotGUI(root, api_key, api_secret)
    root.mainloop()