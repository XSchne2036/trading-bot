import tkinter as tk
from gui import KrakenBotGUI
from config import setup_api_credentials
import logging

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

        # Erstelle eine Instanz der KrakenBotGUI und übergebe die API-Schlüssel
        app = KrakenBotGUI(root, api_key, api_secret)

        # Starte die Hauptereignisschleife
        logging.info("GUI initialized. Starting main loop...")
        root.mainloop()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()