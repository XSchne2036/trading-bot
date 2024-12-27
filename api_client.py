import krakenex
import logging
from typing import Dict, List, Optional

class KrakenAPIClient:
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialisiert den Kraken API-Client mit den angegebenen API-Schlüsseln.

        :param api_key: Der API-Schlüssel für die Kraken API.
        :param api_secret: Das API-Geheimnis für die Kraken API.
        """
        self.api = krakenex.API(key=api_key, secret=api_secret)
        logging.info("Connected to Kraken API.")

    def check_balance(self, favorites: List[str]) -> Dict[str, float]:
        """
        Ruft den Kontostand für die angegebenen Favoriten-Paare ab.

        :param favorites: Eine Liste von Favoriten-Paaren (z. B. ['ADAEUR', 'CQTEUR']).
        :return: Ein Dictionary mit den verfügbaren Beträgen für die Favoriten-Paare.
        """
        try:
            logging.info("Fetching balance...")
            balance = self.api.query_private('Balance')
            logging.info(f"Balance response: {balance}")
            if 'result' in balance:
                valid_balance = {}
                for asset, amount in balance['result'].items():
                    pair = f"{asset}EUR"
                    if pair in favorites:
                        try:
                            amount_float = float(amount)
                            if amount_float >= 0.0001:
                                valid_balance[asset] = amount_float
                        except ValueError:
                            logging.warning(f"Invalid value for {asset}: {amount}")
                logging.info(f"Valid balance: {valid_balance}")
                return valid_balance
            else:
                logging.error(f"Error fetching balance: {balance}")
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
        return {}

    def get_market_price(self, pair: str) -> Optional[float]:
        """
        Ruft den aktuellen Marktpreis für ein bestimmtes Paar ab.

        :param pair: Das HandelsPaar (z. B. 'CQTEUR').
        :return: Der aktuelle Marktpreis oder None, falls ein Fehler auftritt.
        """
        try:
            response = self.api.query_public('Ticker', {'pair': pair.replace("/", "")})
            if response['error']:
                return None
            ticker_info = list(response['result'].values())[0]
            market_price = float(ticker_info['c'][0])
            return market_price
        except Exception as e:
            logging.error(f"Error fetching market price for {pair}: {e}")
        return None

    def get_buy_price(self, pair: str) -> Optional[float]:
        """
        Ruft den Kaufpreis für ein bestimmtes Paar aus der Handelshistorie ab.

        :param pair: Das HandelsPaar (z. B. 'CQTEUR').
        :return: Der Kaufpreis oder None, falls kein Kauf gefunden wird.
        """
        try:
            logging.info(f"Fetching order history for {pair}...")
            response = self.api.query_private('TradesHistory', {'pair': pair.replace("/", "")})
            if 'error' in response and response['error']:
                logging.error(f"Error fetching order history: {response['error']}")
                return None
            trades = response.get('result', {}).get('trades', {})
            if not trades:
                logging.warning(f"No trades found for {pair}.")
                return self.get_market_price(pair)  # Fallback to market price
            buy_price = None
            for trade_id, trade_data in trades.items():
                if trade_data['type'] == 'buy' and trade_data['pair'] == pair:
                    buy_price = float(trade_data['price'])
                    break
            if buy_price is None:
                logging.warning(f"No buy price found for {pair}.")
                return self.get_market_price(pair)  # Fallback to market price
            return buy_price
        except Exception as e:
            logging.error(f"Error fetching buy price for {pair}: {e}")
        return None

    def execute_trade(self, pair: str, volume: float, side: str = 'buy') -> Optional[Dict]:
        """
        Führt einen Trade für ein bestimmtes Paar aus.

        :param pair: Das HandelsPaar (z. B. 'CQTEUR').
        :param volume: Das Handelsvolumen.
        :param side: Die Handelsseite ('buy' oder 'sell').
        :return: Das Ergebnis des Trades oder None, falls ein Fehler auftritt.
        """
        try:
            response = self.api.query_private('AddOrder', {
                'pair': pair,
                'type': side,
                'ordertype': 'market',
                'volume': str(volume)
            })
            if 'result' in response:
                logging.info(f"Trade executed: {response['result']}")
                return response['result']
            else:
                error_message = response.get('error', 'Unknown error')
                logging.error(f"Error executing trade: {error_message}")
                raise Exception(f"Trade execution failed: {error_message}")
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            raise