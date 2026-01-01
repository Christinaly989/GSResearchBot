import json
import os

class WatchlistManager:
    def __init__(self, filepath="watchlist.json"):
        self.filepath = filepath
        self.watchlist = self.load_watchlist()

    def load_watchlist(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_watchlist(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, indent=4)
        except Exception as e:
            print(f"Error saving watchlist: {e}")

    def add_ticker(self, ticker):
        ticker = ticker.strip().upper()
        if ticker and ticker not in self.watchlist:
            self.watchlist.append(ticker)
            self.save_watchlist()
            return True
        return False

    def remove_ticker(self, ticker):
        ticker = ticker.strip().upper()
        if ticker in self.watchlist:
            self.watchlist.remove(ticker)
            self.save_watchlist()
            return True
        return False

    def get_watchlist(self):
        return self.watchlist
