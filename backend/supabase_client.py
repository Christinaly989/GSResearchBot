import os
import streamlit as st
from supabase import create_client, Client

class SupabaseHelper:
    _instance = None
    
    @staticmethod
    def get_client() -> Client:
        if SupabaseHelper._instance is None:
            # Try to get from Streamlit secrets first, then env vars
            try:
                url = st.secrets["SUPABASE_URL"]
                key = st.secrets["SUPABASE_KEY"]
            except (FileNotFoundError, KeyError):
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_KEY")
            
            if not url or not key:
                # If credentials are missing, we cannot connect. 
                # Raise explicit error so user knows what to do.
                raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY in .streamlit/secrets.toml or environment variables.")
                
            SupabaseHelper._instance = create_client(url, key)
            
        return SupabaseHelper._instance
