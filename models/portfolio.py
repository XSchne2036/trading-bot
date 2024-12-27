import json
import os
from typing import Dict, Any

class Portfolio:
    def __init__(self, portfolio_file: str = "portfolio.json"):
        """
        Initialisiert das Portfolio mit der angegebenen Portfolio-Datei.

        :param portfolio_file: Der Pfad zur Datei, in der das Portfolio gespeichert wird.
        """
        self.portfolio_file = portfolio_file
        if os.path.exists(portfolio_file):
            with open(portfolio_file, 'r') as f:
                self.portfolio = json.load(f)
        else:
            self.portfolio = {}

    def save_portfolio(self):
        """
        Speichert das Portfolio in der angegebenen Datei.
        """
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=4)
        print(f"Portfolio saved to {self.portfolio_file}")

    def add_asset(self, asset: str, amount: float):
        """
        Fügt ein Asset zum Portfolio hinzu oder aktualisiert den Betrag, falls das Asset bereits vorhanden ist.

        :param asset: Das Asset (z. B. 'BTC').
        :param amount: Der Betrag des Assets.
        """
        if asset in self.portfolio:
            self.portfolio[asset] += amount
        else:
            self.portfolio[asset] = amount
        print(f"Added {amount} of {asset} to the portfolio.")

    def remove_asset(self, asset: str, amount: float):
        """
        Entfernt ein Asset aus dem Portfolio oder reduziert den Betrag, falls das Asset vorhanden ist.

        :param asset: Das Asset (z. B. 'BTC').
        :param amount: Der Betrag des Assets, der entfernt werden soll.
        """
        if asset in self.portfolio:
            if self.portfolio[asset] >= amount:
                self.portfolio[asset] -= amount
                if self.portfolio[asset] == 0:
                    del self.portfolio[asset]
                print(f"Removed {amount} of {asset} from the portfolio.")
            else:
                print(f"Not enough {asset} in the portfolio.")
        else:
            print(f"{asset} not found in the portfolio.")

    def get_portfolio(self) -> Dict[str, float]:
        """
        Gibt das gesamte Portfolio zurück.

        :return: Ein Dictionary mit den Assets und ihren Beträgen.
        """
        return self.portfolio

    def get_asset_amount(self, asset: str) -> float:
        """
        Gibt den Betrag eines bestimmten Assets im Portfolio zurück.

        :param asset: Das Asset (z. B. 'BTC').
        :return: Der Betrag des Assets oder 0, falls das Asset nicht vorhanden ist.
        """
        return self.portfolio.get(asset, 0.0)

    def clear_portfolio(self):
        """
        Löscht das gesamte Portfolio.
        """
        self.portfolio = {}
        print("Portfolio cleared.")