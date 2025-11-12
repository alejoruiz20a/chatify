import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()

class AuthManager:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")  # TU client_id
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")  # TU client_secret
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")  # TU redirect_uri
        
        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="user-library-read user-top-read playlist-read-private user-read-recently-played",
            cache_path=None,
            show_dialog=True
        )
    
    def get_auth_url(self):
        """Generate authorization URL for users"""
        return self.sp_oauth.get_authorize_url()
    
    def get_access_token(self, code):
        """Exchange authorization code for access token"""
        try:
            token_info = self.sp_oauth.get_access_token(code)
            return token_info
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def refresh_token(self, refresh_token):
        """Refreshes an expired token"""
        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        
        try:
            token_info = auth_manager.refresh_access_token(refresh_token)
            return token_info
        except Exception as e:
            st.error(f"Error refreshing token: {e}")
            return None
    
    def is_token_expired(self, token_info):
        """Checks if token has expired"""
        if not token_info:
            return True
        
        import time
        now = int(time.time())
        return token_info['expires_at'] - now < 60
    
    def get_spotify_client(self, token_info):
        """Creates a Spotify client with user token"""
        if self.is_token_expired(token_info):
            token_info = self.refresh_token(token_info['refresh_token'])
            if token_info:
                st.session_state.token_info = token_info
        
        if token_info:
            return spotipy.Spotify(auth=token_info['access_token'])
        return None
    
    def get_user_id(self, token_info):
        """Get user ID quickly with a single API call"""
        try:
            sp = self.get_spotify_client(token_info)
            if sp:
                profile = sp.current_user()
                return profile.get('id', 'unknown_user')
        except Exception as e:
            print(f"Error getting user ID: {e}")
        return 'unknown_user'