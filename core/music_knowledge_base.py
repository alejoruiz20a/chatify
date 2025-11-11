from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from collections import Counter
import json
import uuid

class MusicKnowledgeBase:
    def __init__(self, persist_directory="./chroma_music_db"):
        self.persist_directory = persist_directory
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
    
    def initialize_knowledge_base(self, music_data):
        documents = self._create_documents(music_data)
        
        documents_with_ids = []
        for doc in documents:
            doc_dict = {
                'page_content': doc.page_content,
                'metadata': doc.metadata,
                'id': str(uuid.uuid4())
            }
            documents_with_ids.append(Document(**doc_dict))
        
        self.vector_store = Chroma.from_documents(
            documents=documents_with_ids,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory
        )
        
        return self.vector_store
    
    def _create_documents(self, music_data):
        documents = []
        
        profile = music_data.get('user_profile', {})
        profile_summary = self._create_profile_summary(music_data)
        profile_summary = f"Username: {profile.get('display_name', 'User')}\n{profile_summary}"
        documents.append(Document(
            page_content=profile_summary,
            metadata={"type": "user_profile"}
        ))
        
        for artist_id, artist_info in music_data.get('artists_info', {}).items():
            content = f"ARTIST: {artist_info['name']}\nGenres: {', '.join(artist_info.get('genres', []))}\nPopularity: {artist_info.get('popularity', 0)}"
            documents.append(Document(
                page_content=content,
                metadata={"type": "artist", "artist_name": artist_info['name']}
            ))
        
        print(music_data.get('saved_tracks', []))
        for track in music_data.get('saved_tracks', []):
            artists_str = ', '.join(track.get('artists', []))
            content = f"SAVED SONG: {track['name']}\nArtists: {artists_str}\nAlbum: {track['album']}"
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "saved_track",
                    "track_name": track['name'],
                    "artists": artists_str
                }
            ))

        for track in music_data.get('top_tracks', []):
            artists_str = ', '.join(track.get('artists', []))
            content = f"FAVORITE SONG (TOP): {track['name']}\nArtists: {artists_str}\nAlbum: {track['album']}\nPopularity: {track.get('popularity', 0)}"
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "top_track",
                    "track_name": track['name'],
                    "artists": artists_str
                }
            ))

        return documents
    
    def _create_profile_summary(self, music_data):
        all_genres = []
        for artist in music_data.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(5)
        
        top_artists = ', '.join([a['name'] for a in music_data.get('top_artists', [])[:10]])
        genres = ', '.join([g for g, _ in top_genres])
        
        return f"""Favorite artists: {top_artists}
            Main genres: {genres}
            Total saved songs: {len(music_data.get('saved_tracks', []))}
            Total playlists: {len(music_data.get('playlists', []))}"""
    
    def get_retriever(self, k=5):
        return self.vector_store.as_retriever(search_kwargs={"k": k})
    
    def search(self, query, k=5):
        return self.vector_store.similarity_search(query, k=k)