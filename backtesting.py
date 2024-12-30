import backtrader as bt
from datetime import datetime

class MyStrategy(bt.Strategy):
    def __init__(self):
        """
        Initialisiert die Handelsstrategie.
        """
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=15)

    def next(self):
        """
        Führt die Handelslogik aus.
        """
        if self.sma > self.data.close:
            self.buy()
        elif self.sma < self.data.close:
            self.sell()

def run_backtest():
    """
    Führt das Backtesting der Strategie aus.
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyStrategy)
    data = bt.feeds.YahooFinanceData(dataname="BTC-USD", fromdate=datetime(2020, 1, 1), todate=datetime(2023, 1, 1))
    cerebro.adddata(data)
    cerebro.run()

if __name__ == '__main__':
    run_backtest()