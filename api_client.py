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
        Ruft den Kontostand für die angegebenen Favoriten-Paare ab, inklusive Funding Wallet.

        :param favorites: Eine Liste von Favoriten-Paaren (z. B. ['ADAEUR', 'CQTEUR']).
        :return: Ein Dictionary mit den verfügbaren Beträgen für die Favoriten-Paare.
        """
        try:
            logging.info("Fetching balance...")
            balance = self.api.query_private('Balance')
            logging.info(f"Balance response: {balance}")

            # Füge das Funding Wallet hinzu
            funding_balance = self.api.query_private('TradeBalance', {'asset': 'ZEUR'})
            logging.info(f"Funding balance response: {funding_balance}")

            valid_balance = {}
            if 'result' in balance:
                for asset, amount in balance['result'].items():
                    pair = f"{asset}EUR"
                    if pair in favorites:
                        try:
                            amount_float = float(amount)
                            if amount_float >= 0.0001:
                                valid_balance[asset] = amount_float
                        except ValueError:
                            logging.warning(f"Invalid value for {asset}: {amount}")

            if 'result' in funding_balance:
                for asset, amount in funding_balance['result'].items():
                    if asset.endswith('.F'):  # Nur Funding-Wallet-Assets
                        base_asset = asset.replace('.F', '')
                        pair = f"{base_asset}EUR"
                        if pair in favorites:
                            try:
                                amount_float = float(amount)
                                if amount_float >= 0.0001:
                                    valid_balance[base_asset] = valid_balance.get(base_asset, 0) + amount_float
                            except ValueError:
                                logging.warning(f"Invalid value for {asset}: {amount}")

            logging.info(f"Valid balance: {valid_balance}")
            return valid_balance
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

    def get_trades_history(self, pair: Optional[str] = None) -> List[Dict]:
        """
        Ruft die Handelshistorie ab und filtert optional nach einem spezifischen Handelspaar.

        :param pair: Das Handelspaar, nach dem gefiltert werden soll (z. B. 'CQTEUR').
                    Wenn None, werden alle Trades zurückgegeben.
        :return: Eine Liste von Trades für das angegebene Paar oder alle Trades.
        """
        try:
            logging.info(f"Fetching trades history for {pair if pair else 'all pairs'}...")
            response = self.api.query_private('TradesHistory')
            if 'error' in response and response['error']:
                logging.error(f"Error fetching trades history: {response['error']}")
                return []
            trades = response.get('result', {}).get('trades', {})
            if not trades:
                logging.warning("No trades found.")
                return []
            if pair:
                # Filtere die Trades nach dem angegebenen Paar
                filtered_trades = [
                    trade_data for trade_data in trades.values()
                    if trade_data.get('pair') == pair
                ]
                logging.info(f"Found {len(filtered_trades)} trades for {pair}.")
                return filtered_trades
            else:
                # Gib alle Trades zurück, wenn kein Paar angegeben ist
                logging.info(f"Found {len(trades)} trades.")
                return list(trades.values())
        except Exception as e:
            logging.error(f"Error fetching trades history: {e}")
        return []

    def execute_trade(self, pair, volume, side, oflags='fcib'):
        """
        Führt einen Trade aus.

        :param pair: Das Handelspaar (z. B. 'ADAEUR').
        :param volume: Das Handelsvolumen.
        :param side: Die Handelsseite ('buy' oder 'sell').
        :param oflags: Optionale Flags (z. B. 'fcib,margin' für Margin-Trading).
        :return: Das Ergebnis des Trades oder None, falls ein Fehler auftritt.
        """
        try:
            response = self.api.query_private('AddOrder', {
                'pair': pair,
                'type': side,
                'ordertype': 'market',
                'volume': str(volume),
                'oflags': oflags
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