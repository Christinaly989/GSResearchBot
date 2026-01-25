import json
import os
from supabase_client import SupabaseHelper

class WatchlistManager:
    def __init__(self, username=None, use_supabase=True):
        self.username = username
        self.use_supabase = use_supabase
        self.supabase = None
        self.watchlist = []

        if self.use_supabase:
            try:
                self.supabase = SupabaseHelper.get_client()
            except Exception:
                self.use_supabase = False
        
        # Determine filepath for local fallback
        if self.username:
            safe_username = "".join([c for c in self.username if c.isalnum() or c in "-_"])
            self.filepath = f"watchlist_{safe_username}.json"
        else:
            self.filepath = "watchlist.json"
            
        self.load_watchlist()

    def load_watchlist(self):
        if self.use_supabase and self.username:
            try:
                # Query 'watchlists' table for this user
                response = self.supabase.table("watchlists").select("ticker").eq("username", self.username).execute()
                if response.data:
                    self.watchlist = [item['ticker'] for item in response.data]
                else:
                    self.watchlist = []
            except Exception as e:
                print(f"Supabase watchlist load error: {e}")
                self.watchlist = [] # Fallback to empty list or local?
        else:
            # Local JSON Fallback
            if not os.path.exists(self.filepath):
                self.watchlist = []
            else:
                try:
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        self.watchlist = json.load(f)
                except Exception:
                    self.watchlist = []
        return self.watchlist

    def add_ticker(self, ticker):
        ticker = ticker.strip().upper()
        if not ticker:
            return False
            
        if ticker in self.watchlist:
            return False

        if self.use_supabase and self.username:
            try:
                self.supabase.table("watchlists").insert({"username": self.username, "ticker": ticker}).execute()
                self.watchlist.append(ticker)
                return True
            except Exception as e:
                print(f"Supabase add ticker error: {e}")
                return False
        else:
            self.watchlist.append(ticker)
            self.save_local_watchlist()
            return True

    def remove_ticker(self, ticker):
        ticker = ticker.strip().upper()
        if ticker not in self.watchlist:
            return False

        if self.use_supabase and self.username:
            try:
                self.supabase.table("watchlists").delete().eq("username", self.username).eq("ticker", ticker).execute()
                self.watchlist.remove(ticker)
                return True
            except Exception as e:
                print(f"Supabase remove ticker error: {e}")
                return False
        else:
            self.watchlist.remove(ticker)
            self.save_local_watchlist()
            return True

    def save_local_watchlist(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, indent=4)
        except Exception as e:
            print(f"Error saving watchlist: {e}")

    def get_watchlist(self):
        return self.watchlist
