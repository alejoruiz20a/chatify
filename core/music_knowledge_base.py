from langchain_community.vectorstores import Weaviate
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from collections import Counter
import weaviate
import os

class MusicKnowledgeBase:
    def __init__(self, user_id=None):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self.user_id = user_id or "default_user"
        
    def _get_weaviate_client(self):
        """Get Weaviate client using the community integration"""
        
        client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
            additional_headers={
                "X-HuggingFace-Api-Key": os.getenv("HUGGINGFACE_API_KEY", "")
            }
        )
        return client
    
    def initialize_knowledge_base(self, music_data):
        """Initialize Weaviate with music data for specific user"""
        client = self._get_weaviate_client()
        
        # Create class name with user ID for multi-tenancy
        class_name = f"MusicProfile_{self.user_id.replace('-', '_')}"
        
        # Check if class exists, if not create it
        if not client.schema.exists(class_name):
            self._create_schema(client, class_name)
        
        documents = self._create_documents(music_data)
        
        # Create vector store with user-specific class
        self.vector_store = Weaviate(
            client=client,
            index_name=class_name,
            text_key="content",
            embedding=self.embedding_model,
            by_text=False,
            attributes=["type", "artist_name", "track_name", "artists", "user_id"]
        )
        
        # Add documents to Weaviate
        self.vector_store.add_documents(documents)
        
        return self.vector_store
    
    def _create_schema(self, client, class_name):
        """Create Weaviate schema for music data with user isolation"""
        schema = {
            "class": class_name,
            "description": f"Music profile for user {self.user_id}",
            "vectorizer": "none",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The content of the document",
                },
                {
                    "name": "type",
                    "dataType": ["text"],
                    "description": "Type of document",
                },
                {
                    "name": "artist_name",
                    "dataType": ["text"],
                    "description": "Name of the artist",
                },
                {
                    "name": "track_name",
                    "dataType": ["text"],
                    "description": "Name of the track",
                },
                {
                    "name": "artists",
                    "dataType": ["text"],
                    "description": "Artists associated with the track",
                },
                {
                    "name": "user_id",
                    "dataType": ["text"],
                    "description": "ID of the user",
                }
            ]
        }
        
        client.schema.create_class(schema)
    
    def _create_documents(self, music_data):
        documents = []
        
        # User profile document
        profile_summary = self._create_profile_summary(music_data)
        user_name = music_data.get('user_profile', {}).get('display_name', 'User')
        profile_content = f"Username: {user_name}\n{profile_summary}"
        
        documents.append(Document(
            page_content=profile_content,
            metadata={
                "type": "user_profile",
                "user_id": self.user_id
            }
        ))
        
        # Artists documents
        for artist_id, artist_info in music_data.get('artists_info', {}).items():
            content = f"ARTIST: {artist_info['name']}\nGenres: {', '.join(artist_info.get('genres', []))}\nPopularity: {artist_info.get('popularity', 0)}"
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "artist", 
                    "artist_name": artist_info['name'],
                    "user_id": self.user_id
                }
            ))
        
        # Saved tracks documents
        for track in music_data.get('saved_tracks', []):
            artists_str = ', '.join(track.get('artists', []))
            content = f"SAVED SONG: {track['name']}\nArtists: {artists_str}\nAlbum: {track['album']}"
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "saved_track",
                    "track_name": track['name'],
                    "artists": artists_str,
                    "user_id": self.user_id
                }
            ))

        # Top tracks documents
        for track in music_data.get('top_tracks', []):
            artists_str = ', '.join(track.get('artists', []))
            content = f"FAVORITE SONG (TOP): {track['name']}\nArtists: {artists_str}\nAlbum: {track['album']}\nPopularity: {track.get('popularity', 0)}"
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "top_track",
                    "track_name": track['name'],
                    "artists": artists_str,
                    "user_id": self.user_id
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
    
    def delete_user_data(self):
        """Delete all data for this user"""
        if self.vector_store and self.client:
            class_name = f"MusicProfile_{self.user_id.replace('-', '_')}"
            self.client.schema.delete_class(class_name)