import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from collections import Counter
import os

class MusicKnowledgeBase:
    def __init__(self, user_id=None):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.client = None
        self.user_id = user_id or "default_user"
        self.collection_name = f"MusicProfile_{self.user_id.replace('-', '_')}"
        
    def _get_weaviate_client(self):
        """Get Weaviate v4 client"""
        if self.client is None:
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=os.getenv("WEAVIATE_URL"),
                auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WEAVIATE_API_KEY")),
            )
        return self.client
    
    def collection_exists(self, use_cache=True):
        """Check if user's collection already exists (with caching)"""
        cache_file = f".weaviate_cache_{self.user_id.replace('-', '_')}.txt"
        
        # Check local cache first (fastest)
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_name = f.read().strip()
                    if cached_name == self.collection_name:
                        print(f"[CACHE HIT] Collection {self.collection_name} found in cache")
                        return True
            except Exception as e:
                print(f"Error reading cache: {e}")
        
        # If not in cache, check Weaviate
        print(f"[CACHE MISS] Querying Weaviate for collection {self.collection_name}")
        try:
            client = self._get_weaviate_client()
            exists = client.collections.exists(self.collection_name)
            
            # Cache the result if collection exists
            if exists:
                self._update_cache()
            else:
                # Clear cache if collection doesn't exist
                self._clear_cache()
            
            return exists
        except Exception as e:
            print(f"Error checking collection existence: {e}")
            return False
    
    def initialize_knowledge_base(self, music_data, force_recreate=False):
        """
        Initialize Weaviate with music data for specific user
        Args:
            music_data: User's music data
            force_recreate: If True, delete existing collection and recreate
        """
        client = self._get_weaviate_client()
        
        # If force_recreate, delete existing collection and clear cache
        if force_recreate:
            # Don't use cache when force recreating
            if self.collection_exists(use_cache=False):
                print(f"Deleting existing collection: {self.collection_name}")
                client.collections.delete(self.collection_name)
                self._clear_cache()
        
        # Check if collection exists (use cache for speed)
        if not self.collection_exists(use_cache=True):
            print(f"Creating new collection: {self.collection_name}")
            self._create_collection(client)
            
            # Add documents only if collection is new
            documents = self._create_documents(music_data)
            self._add_documents_to_collection(client, documents)
            
            # Update cache after successful creation
            self._update_cache()
        else:
            print(f"Collection {self.collection_name} already exists. Skipping initialization.")
        
        return client
    
    def update_knowledge_base(self, music_data):
        """
        Update knowledge base by recreating it with fresh data
        """
        return self.initialize_knowledge_base(music_data, force_recreate=True)
    
    def _create_collection(self, client):
        """Create Weaviate collection with proper schema for music data"""
        client.collections.create(
            name=self.collection_name,
            description=f"Music profile for user {self.user_id}",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(
                    name="content",
                    data_type=DataType.TEXT,
                    description="The content of the document"
                ),
                Property(
                    name="type",
                    data_type=DataType.TEXT,
                    description="Type of document (user_profile, artist, saved_track, top_track)"
                ),
                Property(
                    name="artist_name",
                    data_type=DataType.TEXT,
                    description="Name of the artist"
                ),
                Property(
                    name="track_name",
                    data_type=DataType.TEXT,
                    description="Name of the track"
                ),
                Property(
                    name="artists",
                    data_type=DataType.TEXT,
                    description="Artists associated with the track"
                ),
                Property(
                    name="user_id",
                    data_type=DataType.TEXT,
                    description="ID of the user"
                )
            ]
        )
    
    def _add_documents_to_collection(self, client, documents):
        """Add documents to Weaviate collection"""
        collection = client.collections.get(self.collection_name)
        
        # Prepare data objects for batch insert
        data_objects = []
        for doc in documents:
            # Generate embedding
            embedding = self.embedding_model.embed_query(doc.page_content)
            
            # Prepare properties
            properties = {
                "content": doc.page_content,
                "type": doc.metadata.get("type", ""),
                "artist_name": doc.metadata.get("artist_name", ""),
                "track_name": doc.metadata.get("track_name", ""),
                "artists": doc.metadata.get("artists", ""),
                "user_id": doc.metadata.get("user_id", self.user_id)
            }
            
            data_objects.append({
                "properties": properties,
                "vector": embedding
            })
        
        # Batch insert
        with collection.batch.dynamic() as batch:
            for obj in data_objects:
                batch.add_object(
                    properties=obj["properties"],
                    vector=obj["vector"]
                )
    
    def _create_documents(self, music_data):
        """Create Document objects from music data"""
        documents = []
        
        # User profile document
        profile_summary = self._create_profile_summary(music_data)
        user_name = music_data.get('user_profile', {}).get('display_name', 'User')
        profile_content = f"Username: {user_name}\n{profile_summary}"
        
        documents.append(Document(
            page_content=profile_content,
            metadata={
                "type": "user_profile",
                "user_id": self.user_id,
                "artist_name": "",
                "track_name": "",
                "artists": ""
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
                    "user_id": self.user_id,
                    "track_name": "",
                    "artists": ""
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
                    "user_id": self.user_id,
                    "artist_name": ""
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
                    "user_id": self.user_id,
                    "artist_name": ""
                }
            ))

        return documents
    
    def _create_profile_summary(self, music_data):
        """Create a summary of user's music profile"""
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
    
    def search(self, query, k=5):
        """
        Search for similar documents in the collection
        Args:
            query: Search query string
            k: Number of results to return
        Returns:
            List of Document objects, or None if there's an error that requires user action
        """
        try:
            client = self._get_weaviate_client()
            
            if not self.collection_exists():
                return []
            
            collection = client.collections.get(self.collection_name)
            
            # Generate query embedding
            query_vector = self.embedding_model.embed_query(query)
            
            # Perform vector search
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=k,
                return_metadata=MetadataQuery(distance=True)
            )
            
            # Convert results to Document objects
            documents = []
            for obj in response.objects:
                documents.append(Document(
                    page_content=obj.properties.get("content", ""),
                    metadata={
                        "type": obj.properties.get("type", ""),
                        "artist_name": obj.properties.get("artist_name", ""),
                        "track_name": obj.properties.get("track_name", ""),
                        "artists": obj.properties.get("artists", ""),
                        "user_id": obj.properties.get("user_id", "")
                    }
                ))
            
            return documents
        except Exception as e:
            error_message = str(e)
            # Check if it's the specific Weaviate error about missing class
            if "could not find class" in error_message.lower() or "MusicProfile" in error_message:
                # Return a special marker to indicate the knowledge base needs to be updated
                raise ValueError("KNOWLEDGE_BASE_NEEDS_UPDATE")
            # For other errors, re-raise them
            raise
    
    def delete_user_data(self):
        """Delete all data for this user"""
        client = self._get_weaviate_client()
        if self.collection_exists(use_cache=False):
            client.collections.delete(self.collection_name)
            self._clear_cache()
            print(f"Deleted collection: {self.collection_name}")
    
    def _update_cache(self):
        """Update local cache file"""
        cache_file = f".weaviate_cache_{self.user_id.replace('-', '_')}.txt"
        try:
            with open(cache_file, 'w') as f:
                f.write(self.collection_name)
        except Exception as e:
            print(f"Error updating cache: {e}")
    
    def _clear_cache(self):
        """Clear local cache file"""
        cache_file = f".weaviate_cache_{self.user_id.replace('-', '_')}.txt"
        try:
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    def close(self):
        """Close Weaviate client connection"""
        if self.client:
            self.client.close()