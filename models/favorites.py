import json
import os
from typing import List
import logging

class Favorites:
    def __init__(self, favorites_file: str = "favorites.json"):
        """
        Initialisiert die Favoriten mit der angegebenen Favoriten-Datei.

        :param favorites_file: Der Pfad zur Datei, in der die Favoriten gespeichert werden.
        """
        self.favorites_file = favorites_file
        if os.path.exists(favorites_file):
            with open(favorites_file, 'r') as f:
                self.favorites = json.load(f)
            logging.info(f"Favorites loaded from {favorites_file}.")
        else:
            self.favorites = []
            logging.warning(f"Favorites file not found. Initializing empty favorites list.")

    def save_favorites(self):
        """
        Speichert die Favoriten in der angegebenen Datei.
        """
        try:
            with open(self.favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=4)
            logging.info(f"Favorites saved to {self.favorites_file}.")
        except Exception as e:
            logging.error(f"Error saving favorites: {e}")
            raise

    def add_favorite(self, pair: str):
        """
        Fügt ein Favoriten-Paar hinzu, falls es noch nicht vorhanden ist.

        :param pair: Das Favoriten-Paar (z. B. 'CQTEUR').
        """
        if pair not in self.favorites:
            self.favorites.append(pair)
            logging.info(f"Added {pair} to favorites.")
            self.save_favorites()
        else:
            logging.warning(f"{pair} is already in favorites.")

    def remove_favorite(self, pair: str):
        """
        Entfernt ein Favoriten-Paar, falls es vorhanden ist.

        :param pair: Das Favoriten-Paar (z. B. 'CQTEUR').
        """
        if pair in self.favorites:
            self.favorites.remove(pair)
            logging.info(f"Removed {pair} from favorites.")
            self.save_favorites()
        else:
            logging.warning(f"{pair} not found in favorites.")

    def get_favorites(self) -> List[str]:
        """
        Gibt die Liste der Favoriten-Paare zurück.

        :return: Eine Liste der Favoriten-Paare.
        """
        return self.favorites

    def clear_favorites(self):
        """
        Löscht alle Favoriten-Paare.
        """
        self.favorites = []
        logging.info("Favorites cleared.")
        self.save_favorites()