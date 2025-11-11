from .spotify_client import SpotifyClient, extract_artist_info, extract_track_info
import json
import time

class MusicDataCollector:
    def __init__(self, token_info=None):
        """
        Initializes the collector using user token
        Args:
            token_info: Dictionary with OAuth token information
        """
        self.spotify_client = SpotifyClient(token_info)
        self.collected_data = {
            'user_profile': {},
            'top_artists': [],
            'top_tracks': [],
            'saved_tracks': [],
            'playlists': [],
            'recently_played': [],
            'artists_info': {}
        }
    
    def collect_all_data(self):
        self.collected_data['user_profile'] = self.spotify_client.get_user_profile()
        self.clean_sensitive_data()
        
        top_artists = self.spotify_client.get_top_artists(limit=30)
        self.collected_data['top_artists'] = [extract_artist_info(a) for a in top_artists['items']]
        
        top_tracks = self.spotify_client.get_top_tracks(limit=30)
        self.collected_data['top_tracks'] = [extract_track_info(t) for t in top_tracks['items']]
        
        saved_tracks = self.spotify_client.get_saved_tracks(limit=50)
        self.collected_data['saved_tracks'] = [extract_track_info(i['track']) for i in saved_tracks['items']]
        
        playlists = self.spotify_client.get_user_playlists(limit=20)
        self.collected_data['playlists'] = [
            {'id': pl['id'], 'name': pl['name'], 'tracks_total': pl['tracks']['total']}
            for pl in playlists['items']
        ]
        
        recent_tracks = self.spotify_client.get_recently_played(limit=50)
        self.collected_data['recently_played'] = [extract_track_info(i['track']) for i in recent_tracks['items']]
        
        self._collect_artist_info()
        
        return self.collected_data
    
    def clean_sensitive_data(self):
        if 'user_profile' not in self.collected_data:
            return
        
        profile = self.collected_data['user_profile']
        for field in ['id', 'external_urls', 'href', 'uri', 'images']:
            profile.pop(field, None)
        
        if 'display_name' in profile:
            profile['display_name'] = profile['display_name'].split()[0]
    
    def _collect_artist_info(self):
        all_artist_ids = set()
        
        for artist in self.collected_data['top_artists']:
            all_artist_ids.add(artist['id'])
        
        for track in self.collected_data['top_tracks'] + self.collected_data['saved_tracks']:
            for artist_id in track['artist_ids']:
                all_artist_ids.add(artist_id)
        
        for artist_id in list(all_artist_ids)[:30]:
            try:
                artist_info = self.spotify_client.get_artist_info(artist_id)
                self.collected_data['artists_info'][artist_id] = extract_artist_info(artist_info)
                time.sleep(0.1)
            except:
                pass
    
    def save_data_to_file(self, filename="user_music_data.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, indent=2, ensure_ascii=False)