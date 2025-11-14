import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time

load_dotenv()

class AuthManager:
    def __init__(self):
        # Estas credenciales SOLO se usan para el OAuth flow
        # NO para hacer requests a la API
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        
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
            token_info = self.sp_oauth.get_access_token(code, as_dict=True)
            return token_info
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def refresh_token_if_needed(self, token_info):
        """
        Refresh token if it's expired or about to expire
        Returns: Updated token_info or original if refresh not needed
        """
        if not token_info:
            return None
        
        # Check if token is expired or will expire in the next 60 seconds
        now = int(time.time())
        expires_at = token_info.get('expires_at', 0)
        
        if expires_at - now < 60:  # Token expired or expires soon
            print("Token expired or expiring soon, refreshing...")
            try:
                refresh_token = token_info.get('refresh_token')
                if not refresh_token:
                    print("No refresh token available")
                    return None
                
                # Use SpotifyOAuth to refresh
                new_token_info = self.sp_oauth.refresh_access_token(refresh_token)
                print("Token refreshed successfully")
                return new_token_info
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None
        
        return token_info
    
    def is_token_expired(self, token_info):
        """Checks if token has expired"""
        if not token_info:
            return True
        
        now = int(time.time())
        expires_at = token_info.get('expires_at', 0)
        return expires_at - now < 60
    
    def get_spotify_client(self, token_info):
        """
        Creates a Spotify client with USER token
        IMPORTANT: This uses the user's access token, NOT developer credentials
        """
        # Refresh token if needed
        token_info = self.refresh_token_if_needed(token_info)
        
        if not token_info:
            return None
        
        # Update session state with refreshed token
        if hasattr(st, 'session_state'):
            st.session_state.token_info = token_info
        
        # Create client with USER'S access token
        return spotipy.Spotify(auth=token_info['access_token'])
    
    def get_user_id(self, token_info):
        """
        Get user ID using the USER'S token
        This will return the ID of the logged-in user, not the developer
        """
        try:
            sp = self.get_spotify_client(token_info)
            if sp:
                profile = sp.current_user()
                user_id = profile.get('id', 'unknown_user')
                print(f"Retrieved user ID: {user_id}")  # Debug
                return user_id
        except Exception as e:
            print(f"Error getting user ID: {e}")
            import traceback
            print(traceback.format_exc())
        return 'unknown_user'