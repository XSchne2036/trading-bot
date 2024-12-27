import keyring
import logging
from typing import Optional, Tuple

def get_api_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Lädt die API-Schlüssel aus einem sicheren Speicher (z. B. dem Schlüsselbund des Betriebssystems).

    :return: Ein Tupel mit dem API-Schlüssel und dem API-Geheimnis. Falls keine Schlüssel gefunden werden, wird (None, None) zurückgegeben.
    """
    try:
        api_key = keyring.get_password('kraken_bot', 'api_key')
        api_secret = keyring.get_password('kraken_bot', 'api_secret')
        if api_key and api_secret:
            logging.info("API credentials loaded from keyring.")
            return api_key, api_secret
        else:
            logging.warning("No API credentials found in keyring.")
            return None, None
    except Exception as e:
        logging.error(f"Error loading API credentials: {e}")
        return None, None

def save_api_credentials(api_key: str, api_secret: str) -> bool:
    """
    Speichert die API-Schlüssel in einem sicheren Speicher (z. B. dem Schlüsselbund des Betriebssystems).

    :param api_key: Der API-Schlüssel.
    :param api_secret: Das API-Geheimnis.
    :return: True, wenn die Schlüssel erfolgreich gespeichert wurden, sonst False.
    """
    try:
        keyring.set_password('kraken_bot', 'api_key', api_key)
        keyring.set_password('kraken_bot', 'api_secret', api_secret)
        logging.info("API credentials saved to keyring.")
        return True
    except Exception as e:
        logging.error(f"Error saving API credentials: {e}")
        return False

def prompt_for_api_credentials() -> Tuple[str, str]:
    """
    Fordert den Benutzer auf, die API-Schlüssel einzugeben.

    :return: Ein Tupel mit dem API-Schlüssel und dem API-Geheimnis.
    """
    api_key = input("Enter your Kraken API Key: ")
    api_secret = input("Enter your Kraken API Secret: ")
    return api_key, api_secret

def setup_api_credentials() -> Tuple[str, str]:
    """
    Versucht, die API-Schlüssel zu laden. Falls keine gefunden werden, fordert sie den Benutzer auf, sie einzugeben, und speichert sie.

    :return: Ein Tupel mit dem API-Schlüssel und dem API-Geheimnis.
    """
    api_key, api_secret = get_api_credentials()
    if not api_key or not api_secret:
        api_key, api_secret = prompt_for_api_credentials()
        if api_key and api_secret:
            save_api_credentials(api_key, api_secret)
        else:
            raise ValueError("API credentials are required.")
    return api_key, api_secret