import os
import json
import krakenex
from time import sleep

# API-Verbindung
api_key = None
api_secret = None
key_path = os.path.join(os.path.dirname(__file__), '..', 'kraken.key')

if os.path.exists(key_path):
    with open(key_path, 'r') as f:
        api_key = f.readline().strip()
        api_secret = f.readline().strip()

if not api_key or not api_secret:
    print("API-Schlüssel fehlen. Bitte stelle sicher, dass die 'kraken.key' Datei vorhanden ist.")
    exit()

api = krakenex.API(key=api_key, secret=api_secret)
print("Verbindung zur Kraken API hergestellt.")

# Datei zur Speicherung des Portfolios
portfolio_file = os.path.join(os.path.dirname(__file__), 'portfolio.json')

# Initiales Portfolio laden
if os.path.exists(portfolio_file):
    with open(portfolio_file, 'r') as f:
        portfolio = json.load(f)
else:
    portfolio = {}

# Speichern des Portfolios
def save_portfolio():
    with open(portfolio_file, 'w') as f:
        json.dump(portfolio, f, indent=4)

# Gebührenrate (Standard Taker-Gebühr bei Kraken)
FEE_RATE = 0.0026

# Kontostand abrufen
def check_balance():
    try:
        print("Abrufen des Kontostands...")
        balance = api.query_private('Balance')
        if 'result' in balance:
            valid_balance = {}
            for asset, amount in balance['result'].items():
                try:
                    amount_float = float(amount)
                    if amount_float >= 0.0001:
                        valid_balance[asset] = amount_float
                except ValueError:
                    print(f"Ungültiger Wert für {asset}: {amount}")
            return valid_balance
        else:
            print("Fehler beim Abrufen des Kontostands:", balance)
    except Exception as e:
        print(f"Fehler beim Abrufen des Kontostands: {e}")
    return {}


# Marktpreis abrufen
def get_market_price(pair):
    try:
        print(f"Abrufen der Marktdaten für {pair}...")
        ticker = api.query_public('Ticker', {'pair': pair})
        if 'result' in ticker:
            price = float(list(ticker['result'].values())[0]['c'][0])  # Schlusskurs
            print(f"Letzter Preis für {pair}: {price}")
            return price
        else:
            print("Fehler beim Abrufen der Marktdaten:", ticker)
    except Exception as e:
        print(f"Fehler beim Abrufen der Marktdaten: {e}")
    return None

# Handel ausführen
def execute_trade(pair, volume, side='buy'):
    try:
        print(f"Starte den Handel: {side} {volume} {pair}...")
        response = api.query_private('AddOrder', {
            'pair': pair,
            'type': side,
            'ordertype': 'market',
            'volume': str(volume)
        })
        if 'result' in response:
            print("Handel erfolgreich durchgeführt:", response['result'])
            return response['result']
        else:
            print("Fehler beim Handel:", response)
    except Exception as e:
        print(f"Fehler beim Ausführen des Handels: {e}")
    return None

# Kauf speichern
def update_portfolio(pair, volume, price):
    asset = pair.split('/')[0]
    if asset in portfolio:
        total_cost = portfolio[asset]['price'] * portfolio[asset]['volume']
        total_cost += price * volume
        total_volume = portfolio[asset]['volume'] + volume
        portfolio[asset]['price'] = total_cost / total_volume
        portfolio[asset]['volume'] = total_volume
    else:
        portfolio[asset] = {'price': price, 'volume': volume}
    save_portfolio()

# Verkauf speichern
def remove_from_portfolio(pair, volume):
    asset = pair.split('/')[0]
    if asset in portfolio:
        portfolio[asset]['volume'] -= volume
        if portfolio[asset]['volume'] <= 0:
            del portfolio[asset]
        save_portfolio()

# Hauptlogik
def main():
    pair = 'INTR/EUR'
    balance = check_balance()
    market_price = get_market_price(pair)
    if not market_price:
        return

    # Handelslogik (einfaches Beispiel)
    if pair.split('/')[0] in portfolio:
        avg_price = portfolio[pair.split('/')[0]]['price']
        if market_price > avg_price * 1.02:  # Verkaufe bei 2% Gewinn
            volume = portfolio[pair.split('/')[0]]['volume']
            trade = execute_trade(pair, volume, side='sell')
            if trade:
                remove_from_portfolio(pair, volume)
    elif 'ZEUR' in balance and balance['ZEUR'] > market_price * 10:
        volume = 10
        trade = execute_trade(pair, volume, side='buy')
        if trade:
            update_portfolio(pair, volume, market_price)

if __name__ == '__main__':
    while True:
        main()
        sleep(30)
