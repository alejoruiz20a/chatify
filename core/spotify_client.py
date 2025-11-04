import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = "http://127.0.0.1:8501/callback"
        
        self.scope = "user-library-read user-top-read playlist-read-private user-read-recently-played"
        
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=".spotify_cache",
            show_dialog=True
        ))
    
    def get_user_profile(self):
        """Obtiene el perfil básico del usuario"""
        return self.sp.current_user()
    
    def get_top_artists(self, limit=20, time_range='medium_term'):
        """Obtiene los artistas más escuchados"""
        actual_limit = min(limit, 50)
        return self.sp.current_user_top_artists(
            limit=actual_limit, 
            time_range=time_range
        )
    
    def get_top_tracks(self, limit=20, time_range='medium_term'):
        """Obtiene las canciones más escuchadas"""
        actual_limit = min(limit, 50)
        return self.sp.current_user_top_tracks(
            limit=actual_limit, 
            time_range=time_range
        )
    
    def get_saved_tracks(self, limit=50):
        """Obtiene las canciones guardadas (Me gusta)"""
        actual_limit = min(limit, 50)
        return self.sp.current_user_saved_tracks(limit=actual_limit)
    
    def get_user_playlists(self, limit=50):
        """Obtiene las playlists del usuario"""
        return self.sp.current_user_playlists(limit=limit)
    
    def get_recently_played(self, limit=50):
        """Obtiene las canciones reproducidas recientemente"""
        return self.sp.current_user_recently_played(limit=limit)
    
    def get_recommendations(self, seed_artists=None, seed_tracks=None, limit=20):
        """Obtiene recomendaciones basadas en artistas o canciones"""
        return self.sp.recommendations(
            seed_artists=seed_artists or [],
            seed_tracks=seed_tracks or [],
            limit=limit
        )
    
    def get_artist_info(self, artist_id):
        """Obtiene información detallada de un artista"""
        return self.sp.artist(artist_id)
    
    def search_artist(self, artist_name, limit=5):
        """Busca artistas por nombre"""
        return self.sp.search(
            q=f'artist:{artist_name}',
            type='artist',
            limit=limit
        )
    
    def get_audio_features(self, track_ids):
        """Obtiene características de audio de las canciones"""
        if not track_ids:
            return []
        return self.sp.audio_features(track_ids)

# Funciones de utilidad para extraer información relevante
def extract_artist_info(artist_data):
    """Extrae información relevante de los datos del artista"""
    return {
        'id': artist_data['id'],
        'name': artist_data['name'],
        'genres': artist_data.get('genres', []),
        'popularity': artist_data.get('popularity', 0),
        'followers': artist_data.get('followers', {}).get('total', 0),
        'uri': artist_data['uri']
    }

def extract_track_info(track_data):
    """Extrae información relevante de los datos de la canción"""
    return {
        'id': track_data['id'],
        'name': track_data['name'],
        'artists': [artist['name'] for artist in track_data['artists']],
        'artist_ids': [artist['id'] for artist in track_data['artists']],
        'album': track_data['album']['name'],
        'duration_ms': track_data['duration_ms'],
        'popularity': track_data.get('popularity', 0),
        'uri': track_data['uri']
    }