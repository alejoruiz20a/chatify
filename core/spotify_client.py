import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self, token_info=None):
        """
        Inicializa el cliente de Spotify con un token de usuario
        Args:
            token_info: Diccionario con la información del token OAuth
        """
        if token_info:
            # Cliente autenticado con token de usuario
            self.sp = spotipy.Spotify(auth=token_info['access_token'])
        else:
            # Fallback al método anterior (para desarrollo)
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri="http://localhost:8501",
                scope="user-library-read user-top-read playlist-read-private user-read-recently-played",
                cache_path=".spotify_cache",
                show_dialog=True
            ))
    
    def get_user_profile(self):
        return self.sp.current_user()
    
    def get_top_artists(self, limit=20, time_range='medium_term'):
        return self.sp.current_user_top_artists(limit=min(limit, 50), time_range=time_range)
    
    def get_top_tracks(self, limit=20, time_range='medium_term'):
        return self.sp.current_user_top_tracks(limit=min(limit, 50), time_range=time_range)
    
    def get_saved_tracks(self, limit=50):
        """
        Obtiene todas las canciones guardadas sin duplicados
        Args:
            limit: Máximo de canciones por request (máx 50 por limitación de Spotify)
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
        return self.sp.current_user_playlists(limit=limit)
    
    def get_recently_played(self, limit=50):
        return self.sp.current_user_recently_played(limit=limit)
    
    def get_recommendations(self, seed_artists=None, seed_tracks=None, limit=20):
        return self.sp.recommendations(
            seed_artists=seed_artists or [],
            seed_tracks=seed_tracks or [],
            limit=limit
        )
    
    def get_artist_info(self, artist_id):
        return self.sp.artist(artist_id)

def extract_artist_info(artist_data):
    return {
        'id': artist_data['id'],
        'name': artist_data['name'],
        'genres': artist_data.get('genres', []),
        'popularity': artist_data.get('popularity', 0),
        'followers': artist_data.get('followers', {}).get('total', 0)
    }

def extract_track_info(track_data):
    return {
        'id': track_data['id'],
        'name': track_data['name'],
        'artists': [artist['name'] for artist in track_data['artists']],
        'artist_ids': [artist['id'] for artist in track_data['artists']],
        'album': track_data['album']['name'],
        'popularity': track_data.get('popularity', 0)
    }