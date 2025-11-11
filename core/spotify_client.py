import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self, token_info):
        """
        Initialize Spotify client with USER token only
        No fallback to developer credentials needed
        """
        if not token_info:
            raise ValueError("User token is required")
        
        # 👇 Solo usa el token del usuario, NO tus credenciales
        self.sp = spotipy.Spotify(auth=token_info['access_token'])
    
    def get_user_profile(self):
        """Get current user's profile information"""
        return self.sp.current_user()
    
    def get_top_artists(self, limit=20, time_range='medium_term'):
        """Get user's top artists"""
        return self.sp.current_user_top_artists(limit=min(limit, 50), time_range=time_range)
    
    def get_top_tracks(self, limit=20, time_range='medium_term'):
        """Get user's top tracks"""
        return self.sp.current_user_top_tracks(limit=min(limit, 50), time_range=time_range)
    
    def get_saved_tracks(self, limit=50):
        """
        Get all saved tracks without duplicates
        Args:
            limit: Maximum tracks per request (max 50 due to Spotify limitations)
        """
        all_tracks = []
        offset = 0
        batch_size = min(limit, 50)
        
        while True:
            results = self.sp.current_user_saved_tracks(limit=batch_size, offset=offset)
            
            if not results['items']:
                break
            
            all_tracks.extend(results['items'])
            
            if len(results['items']) < batch_size:
                break
                
            offset += batch_size
            
            if len(all_tracks) >= 500:
                break
        
        return {'items': all_tracks}
    
    def get_user_playlists(self, limit=50):
        """Get user's playlists"""
        return self.sp.current_user_playlists(limit=limit)
    
    def get_recently_played(self, limit=50):
        """Get user's recently played tracks"""
        return self.sp.current_user_recently_played(limit=limit)
    
    def get_recommendations(self, seed_artists=None, seed_tracks=None, limit=20):
        """Get track recommendations based on seeds"""
        return self.sp.recommendations(
            seed_artists=seed_artists or [],
            seed_tracks=seed_tracks or [],
            limit=limit
        )
    
    def get_artist_info(self, artist_id):
        """Get detailed information for a specific artist"""
        return self.sp.artist(artist_id)

def extract_artist_info(artist_data):
    """Extract relevant artist information from Spotify API response"""
    return {
        'id': artist_data['id'],
        'name': artist_data['name'],
        'genres': artist_data.get('genres', []),
        'popularity': artist_data.get('popularity', 0),
        'followers': artist_data.get('followers', {}).get('total', 0)
    }

def extract_track_info(track_data):
    """Extract relevant track information from Spotify API response"""
    return {
        'id': track_data['id'],
        'name': track_data['name'],
        'artists': [artist['name'] for artist in track_data['artists']],
        'artist_ids': [artist['id'] for artist in track_data['artists']],
        'album': track_data['album']['name'],
        'popularity': track_data.get('popularity', 0)
    }