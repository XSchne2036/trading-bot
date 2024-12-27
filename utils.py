import logging
import tkinter as tk

class TextWidgetHandler(logging.Handler):
    """
    Ein benutzerdefinierter Logging-Handler, der Log-Nachrichten in ein tkinter Text-Widget schreibt.
    """
    def __init__(self, text_widget: tk.Text):
        """
        Initialisiert den Handler mit dem angegebenen Text-Widget.

        :param text_widget: Das tkinter Text-Widget, in das die Log-Nachrichten geschrieben werden sollen.
        """
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        """
        Schreibt die Log-Nachricht in das Text-Widget.

        :param record: Das LogRecord-Objekt, das die Log-Nachricht enthält.
        """
        try:
            msg = self.format(record)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)  # Scrollt zum Ende des Text-Widgets
        except Exception:
            self.handleError(record)

def setup_logging():
    """
    Konfiguriert das Logging-System mit einem Datei-Handler und einem Stream-Handler.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("kraken_bot.log"),  # Log-Nachrichten in eine Datei schreiben
            logging.StreamHandler()  # Log-Nachrichten in die Konsole schreiben
        ]
    )

def get_api_credentials():
    """
    Fordert den Benutzer auf, die API-Schlüssel einzugeben.

    :return: Ein Tupel mit dem API-Schlüssel und dem API-Geheimnis.
    """
    api_key = input("Enter your Kraken API Key: ")
    api_secret = input("Enter your Kraken API Secret: ")
    return api_key, api_secret

def save_api_credentials(api_key: str, api_secret: str):
    """
    Speichert die API-Schlüssel in einem sicheren Speicher (z. B. dem Schlüsselbund des Betriebssystems).

    :param api_key: Der API-Schlüssel.
    :param api_secret: Das API-Geheimnis.
    """
    import keyring
    keyring.set_password('kraken_bot', 'api_key', api_key)
    keyring.set_password('kraken_bot', 'api_secret', api_secret)

def load_api_credentials():
    """
    Lädt die API-Schlüssel aus einem sicheren Speicher.

    :return: Ein Tupel mit dem API-Schlüssel und dem API-Geheimnis.
    """
    import keyring
    api_key = keyring.get_password('kraken_bot', 'api_key')
    api_secret = keyring.get_password('kraken_bot', 'api_secret')
    return api_key, api_secret