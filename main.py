import tkinter as tk
from gui import KrakenBotGUI
from config import setup_api_credentials
import logging
import sys
import pystray
from PIL import Image
import threading


# --- Tray-Icon-Funktionen ---
def minimize_to_tray(window, icon_holder):
    """
    Minimiert das Fenster in das System-Tray.
    """
    window.withdraw()  # Fenster verstecken

    def restore():
        """
        Funktion zum Wiederherstellen des Fensters.
        """
        window.deiconify()  # Fenster wiederherstellen
        icon_holder['icon'].stop()  # Tray-Icon beenden

    # Bild für das Tray-Icon (verwendet das konvertierte PNG)
    try:
        image = Image.open("trading_bot_logo.png")  # Pfad zum Icon-Bild
    except FileNotFoundError:
        logging.warning("Icon-Bild nicht gefunden. Verwende Standard-Icon.")
        image = Image.new('RGB', (64, 64), color='gray')  # Fallback: einfaches graues Icon

    # Tray-Icon erstellen
    menu = pystray.Menu(
        pystray.MenuItem("Fenster wiederherstellen", lambda: restore()),
        pystray.MenuItem("Beenden", lambda: sys.exit())
    )
    icon = pystray.Icon("kraken_bot", image, "Kraken Bot", menu)
    icon_holder['icon'] = icon  # Tray-Icon im Holder speichern
    threading.Thread(target=icon.run, daemon=True).start()


# --- Hauptfunktion ---
def main():
    """
    Hauptfunktion, die die Anwendung startet.
    """
    try:
        # Logging konfigurieren
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("kraken_bot.log"),  # Log-Nachrichten in eine Datei schreiben
                logging.StreamHandler()  # Log-Nachrichten in die Konsole schreiben
            ]
        )
        logging.info("Starting Kraken Bot...")

        # Lade oder fordere die API-Schlüssel an
        api_key, api_secret = setup_api_credentials()
        logging.debug(f"API Key: {api_key}, API Secret: {api_secret}")

        # Initialisiere das Hauptfenster der Anwendung
        root = tk.Tk()
        root.title("Kraken Bot")
        root.geometry("800x600")  # Beispielgröße des Fensters

        # Minimieren-Button (typischer Punkt-Button wie bei Winamp)
        minimize_button = tk.Button(root, text="·", command=lambda: minimize_to_tray(root, icon_holder), width=2)
        minimize_button.place(relx=1.0, x=-10, y=10, anchor="ne")  # Position oben rechts

        # Erstelle eine Instanz der KrakenBotGUI und übergebe die API-Schlüssel
        app = KrakenBotGUI(root, api_key, api_secret)

        # Icon-Holder für Tray-Icon
        icon_holder = {}

        # Starte die Hauptereignisschleife
        logging.info("GUI initialized. Starting main loop...")
        root.mainloop()

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
