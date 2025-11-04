from .spotify_client import SpotifyClient, extract_artist_info, extract_track_info
import json
from typing import Dict, List, Any
import time
from collections import Counter

class MusicDataCollector:
    def __init__(self):
        self.spotify_client = SpotifyClient()
        self.collected_data = {
            'user_profile': {},
            'top_artists': [],
            'top_tracks': [],
            'saved_tracks': [],
            'playlists': [],
            'recently_played': [],
            'artists_info': {},
            'audio_features': {}
        }
    
    def collect_all_data(self) -> Dict[str, Any]:
        print("Comenzando recolección de datos de Spotify...")
        
        try:
            # Perfil de usuario
            self.collected_data['user_profile'] = self.spotify_client.get_user_profile()
            self.clean_sensitive_data()
            print(f"Perfil de {self.collected_data['user_profile']['display_name']} obtenido")
            print(self.collected_data['user_profile'])
            
            # Artistas top
            top_artists = self.spotify_client.get_top_artists(limit=30)
            self.collected_data['top_artists'] = [extract_artist_info(artist) for artist in top_artists['items']]
            print(f"{len(self.collected_data['top_artists'])} artistas top obtenidos")
            
            # Canciones top
            top_tracks = self.spotify_client.get_top_tracks(limit=30)
            self.collected_data['top_tracks'] = [extract_track_info(track) for track in top_tracks['items']]
            print(f"{len(self.collected_data['top_tracks'])} canciones top obtenidas")
            
            # Canciones guardadas
            saved_tracks = self.spotify_client.get_saved_tracks(limit=50)
            self.collected_data['saved_tracks'] = [extract_track_info(item['track']) for item in saved_tracks['items']]
            print(f"{len(self.collected_data['saved_tracks'])} canciones guardadas obtenidas")
            
            # Playlists
            playlists = self.spotify_client.get_user_playlists(limit=20)
            self.collected_data['playlists'] = [
                {
                    'id': pl['id'],
                    'name': pl['name'],
                    'description': pl.get('description', ''),
                    'tracks_total': pl['tracks']['total']
                } for pl in playlists['items']
            ]
            print(f"{len(self.collected_data['playlists'])} playlists obtenidas")
            
            # Recientemente escuchado
            recent_tracks = self.spotify_client.get_recently_played(limit=30)
            self.collected_data['recently_played'] = [extract_track_info(item['track']) for item in recent_tracks['items']]
            print(f"{len(self.collected_data['recently_played'])} canciones recientes obtenidas")
            
            # Información detallada de artistas
            self._collect_detailed_artist_info()
            
            print("Recolección de datos completada!")
            return self.collected_data
            
        except Exception as e:
            print(f"Error durante la recolección: {e}")
            raise
    
    def clean_sensitive_data(self):
        """
        Limpia datos sensibles del perfil de usuario.
        """
        if 'user_profile' not in self.collected_data:
            return
        
        profile = self.collected_data['user_profile']
        
        # 🔴 ELIMINAR datos identificables
        sensitive_fields = [
            'id',              # ID único de Spotify
            'external_urls',   # Links al perfil público
            'href',            # URL de la API
            'uri',             # URI de Spotify
            'images'           # Fotos de perfil (incluyen ID de Facebook)
        ]
        
        for field in sensitive_fields:
            profile.pop(field, None)
        
        # 🟡 ANONIMIZAR nombre (opcional según tu caso de uso)
        if 'display_name' in profile:
            # Opción 1: Solo primer nombre
            profile['display_name'] = profile['display_name'].split()[0]
            
            # Opción 2: Completamente anónimo
            # profile['display_name'] = "Usuario"
        
        print("✅ Datos sensibles eliminados del perfil")
    
    def _collect_detailed_artist_info(self):
        all_artist_ids = set()
        
        for artist in self.collected_data['top_artists']:
            all_artist_ids.add(artist['id'])
        
        for track in self.collected_data['top_tracks'] + self.collected_data['saved_tracks']:
            for artist_id in track['artist_ids']:
                all_artist_ids.add(artist_id)
        
        print(f"Obteniendo información detallada de {len(all_artist_ids)} artistas...")
        
        artist_ids_to_process = list(all_artist_ids)[:30]
        
        for artist_id in artist_ids_to_process:
            try:
                artist_info = self.spotify_client.get_artist_info(artist_id)
                self.collected_data['artists_info'][artist_id] = extract_artist_info(artist_info)
                time.sleep(0.1)
            except Exception as e:
                print(f"Error obteniendo info del artista {artist_id}: {e}")
    
    def save_data_to_file(self, filename="user_music_data.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, indent=2, ensure_ascii=False)
        print(f"Datos guardados en {filename}")
    
    def load_data_from_file(self, filename="user_music_data.json"):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.collected_data = json.load(f)
            print(f"Datos cargados desde {filename}")
            return self.collected_data
        except FileNotFoundError:
            print("Archivo de datos no encontrado")
            return None

    def get_music_profile_summary(self) -> str:
        if not self.collected_data:
            return "No hay datos disponibles"
        
        profile = self.collected_data
        
        all_genres = []
        for artist in profile.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(10)
        
        summary = f"""PERFIL MUSICAL DE {profile['user_profile'].get('display_name', 'Usuario')}

ARTISTAS FAVORITOS:
{', '.join([artist['name'] for artist in profile.get('top_artists', [])[:10]])}

GÉNEROS MÁS ESCUCHADOS:
{', '.join([f"{genre} ({count})" for genre, count in top_genres])}

CANCIONES FAVORITAS:
{', '.join([track['name'] for track in profile.get('top_tracks', [])[:10]])}

TOTAL DE CANCIONES GUARDADAS: {len(profile.get('saved_tracks', []))}
TOTAL DE PLAYLISTS: {len(profile.get('playlists', []))}
"""
        return summary