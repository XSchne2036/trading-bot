import krakenex
import time
import pandas as pd

# API-Setup
api = krakenex.API()
api.load_key('kraken.key')  # Datei mit API-Schlüssel

# RSI-Berechnung
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Marktdaten abrufen
def get_ada_price():
    response = api.query_public('OHLC', {'pair': 'ADAEUR', 'interval': 1})
    if response['error']:
        print("Fehler beim Abrufen der Daten:", response['error'])
        return None
    data = response['result']['XADAZEUR']
    df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'])
    df['close'] = df['close'].astype(float)
    return df

# Handelsstrategie
def trade_logic():
    df = get_ada_price()
    if df is None:
        return
    df['RSI'] = calculate_rsi(df['close'])
    current_rsi = df['RSI'].iloc[-1]
    print(f"Aktueller RSI: {current_rsi}")

    if current_rsi < 30:  # Kaufentscheidung
        print("RSI unter 30. Kaufempfehlung!")
        # api.query_private('AddOrder', {'pair': 'ADAEUR', 'type': 'buy', 'ordertype': 'market', 'volume': '1'})
    elif current_rsi > 70:  # Verkaufsentscheidung
        print("RSI über 70. Verkaufsempfehlung!")
        # api.query_private('AddOrder', {'pair': 'ADAEUR', 'type': 'sell', 'ordertype': 'market', 'volume': '1'})

# Bot-Loop
if __name__ == "__main__":
    while True:
        try:
            trade_logic()
            time.sleep(60)  # 1-Minuten-Intervalle
        except Exception as e:
            print("Fehler:", e)
            time.sleep(60)
