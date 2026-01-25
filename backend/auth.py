import sqlite3
import hashlib
import os
import streamlit as st
from supabase_client import SupabaseHelper

class AuthManager:
    def __init__(self, use_supabase=True):
        self.use_supabase = use_supabase
        self.supabase = None
        
        if self.use_supabase:
            try:
                self.supabase = SupabaseHelper.get_client()
            except Exception:
                # Fallback to local SQLite if Supabase not configured
                self.use_supabase = False
                
        if not self.use_supabase:
            self.db_path = "users.db"
            self.init_local_db()

    def init_local_db(self):
        """Initialize the users database table (SQLite)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                download_path TEXT
            )
        ''')
        # Migration: Add download_path column if it doesn't exist
        try:
            c.execute("ALTER TABLE users ADD COLUMN download_path TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists
            
        conn.commit()
        conn.close()

    def _hash_password(self, password):
        """Hash a password for storing."""
        return hashlib.sha256(password.encode()).hexdigest()

    def get_download_path(self, username):
        """Get user's preferred download path."""
        if self.use_supabase:
            try:
                response = self.supabase.table("users").select("download_path").eq("username", username).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("download_path")
            except Exception as e:
                print(f"Supabase get path error: {e}")
        else:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT download_path FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            conn.close()
            if result:
                return result[0]
        return None

    def set_download_path(self, username, path):
        """Set user's preferred download path."""
        if self.use_supabase:
            try:
                self.supabase.table("users").update({"download_path": path}).eq("username", username).execute()
                return True
            except Exception as e:
                print(f"Supabase set path error: {e}")
                return False
        else:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('UPDATE users SET download_path = ? WHERE username = ?', (path, username))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                print(f"Local set path error: {e}")
                return False

    def register_user(self, username, password):
        """Register a new user. Returns (success, message)."""
        if not username or not password:
            return False, "Username and password cannot be empty."
        
        password_hash = self._hash_password(password)
        
        if self.use_supabase:
            try:
                # Insert into Supabase 'users' table
                data = {"username": username, "password_hash": password_hash}
                self.supabase.table("users").insert(data).execute()
                return True, "User registered successfully (Cloud)."
            except Exception as e:
                # Check for duplicate key error (usually contains '23505')
                if "23505" in str(e) or "duplicate key" in str(e).lower():
                     return False, "Username already exists."
                return False, f"Error registering in Cloud: {e}"
        else:
            # SQLite fallback
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                          (username, password_hash))
                conn.commit()
                conn.close()
                return True, "User registered successfully (Local)."
            except sqlite3.IntegrityError:
                return False, "Username already exists."
            except Exception as e:
                return False, f"Error: {e}"

    def login_user(self, username, password):
        """Verify user credentials. Returns True if valid."""
        password_hash = self._hash_password(password)
        
        if self.use_supabase:
            try:
                response = self.supabase.table("users").select("password_hash").eq("username", username).execute()
                if response.data and len(response.data) > 0:
                    stored_hash = response.data[0]["password_hash"]
                    return stored_hash == password_hash
                return False
            except Exception as e:
                print(f"Supabase login error: {e}")
                return False
        else:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            conn.close()
            
            if result and result[0] == password_hash:
                return True
            return False
