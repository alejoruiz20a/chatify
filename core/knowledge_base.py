from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv
import json
import uuid

load_dotenv()

class MusicKnowledgeBase:
    def __init__(self, persist_directory="./chroma_music_db"):
        self.persist_directory = persist_directory
        
        # Usar embeddings locales
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.vector_store = None
    
    def initialize_knowledge_base(self, music_data):
        """Inicializa la base de conocimiento con datos musicales"""
        print("📚 Inicializando base de conocimiento musical...")
        
        documents = self._create_documents_from_music_data(music_data)
        
        print(f"Creando {len(documents)} documentos para la base de conocimiento...")
        
        # Generar IDs manualmente para compatibilidad
        documents_with_ids = []
        for doc in documents:
            doc_dict = doc.to_dict() if hasattr(doc, 'to_dict') else {
                'page_content': doc.page_content,
                'metadata': doc.metadata
            }
            doc_dict["id"] = str(uuid.uuid4())
            documents_with_ids.append(Document(**doc_dict))
        
        self.vector_store = Chroma.from_documents(
            documents=documents_with_ids,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory
        )
        
        print(f"Base de conocimiento creada con {len(documents)} documentos")
        return self.vector_store
    
    def _create_documents_from_music_data(self, music_data) -> list:
        """Crea documentos LangChain a partir de los datos musicales"""
        documents = []
        
        # Documento de perfil de usuario
        profile_summary = self._create_profile_summary(music_data)
        documents.append(Document(
            page_content=profile_summary,
            metadata={"type": "user_profile", "source": "spotify"}
        ))
        
        # Documentos de artistas
        for artist_id, artist_info in music_data.get('artists_info', {}).items():
            artist_doc = self._create_artist_document(artist_info)
            documents.append(artist_doc)
        
        # Documentos de géneros musicales
        genre_docs = self._create_genre_documents(music_data)
        documents.extend(genre_docs)
        
        return documents
    
    def _create_profile_summary(self, music_data) -> str:
        """Crea un resumen del perfil musical del usuario"""
        profile = music_data
        
        all_genres = []
        for artist in profile.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        from collections import Counter
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(5)
        
        summary = f"""PERFIL MUSICAL DE {profile['user_profile'].get('display_name', 'Usuario')}

ARTISTAS FAVORITOS:
{', '.join([artist['name'] for artist in profile.get('top_artists', [])[:10]])}

GÉNEROS PREFERIDOS:
{', '.join([genre for genre, count in top_genres])}

ESTILO MUSICAL GENERAL:
El usuario muestra preferencia por artistas diversos con énfasis en {top_genres[0][0] if top_genres else 'varios géneros'}.

HISTORIAL DE ESCUCHA:
- {len(profile.get('saved_tracks', []))} canciones guardadas como favoritas
- {len(profile.get('playlists', []))} playlists creadas
- Activo recientemente escuchando {len(profile.get('recently_played', []))} canciones
"""
        return summary
    
    def _create_artist_document(self, artist_info) -> Document:
        """Crea un documento para un artista"""
        content = f"""ARTISTA: {artist_info['name']}

INFORMACIÓN:
- Géneros: {', '.join(artist_info.get('genres', []))}
- Popularidad: {artist_info.get('popularity', 0)}/100
- Seguidores: {artist_info.get('followers', 0):,}

ESTILO MUSICAL:
{artist_info['name']} es conocido por su trabajo en los géneros {', '.join(artist_info.get('genres', ['variados']))}."""
        
        return Document(
            page_content=content,
            metadata={
                "type": "artist",
                "artist_id": artist_info['id'],
                "artist_name": artist_info['name'],
                "genres": json.dumps(artist_info.get('genres', [])),
                "source": "spotify"
            }
        )
    
    def _create_genre_documents(self, music_data) -> list:
        """Crea documentos para los géneros musicales del usuario"""
        documents = []
        
        all_genres = set()
        for artist in music_data.get('top_artists', []):
            all_genres.update(artist.get('genres', []))
        
        for genre in list(all_genres)[:15]:
            content = f"""GÉNERO MUSICAL: {genre}

ARTISTAS RELACIONADOS EN LA COLECCIÓN:
{', '.join([artist['name'] for artist in music_data.get('top_artists', []) if genre in artist.get('genres', [])][:5])}"""
            
            documents.append(Document(
                page_content=content,
                metadata={
                    "type": "genre",
                    "genre_name": genre,
                    "source": "spotify_derived"
                }
            ))
        
        return documents
    
    def get_retriever(self, search_type="similarity", k=5):
        """Obtiene el retriever para búsquedas"""
        if self.vector_store is None:
            raise ValueError("La base de conocimiento no ha sido inicializada")
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
    
    def search(self, query: str, k: int = 5):
        """Busca en la base de conocimiento"""
        if self.vector_store is None:
            raise ValueError("La base de conocimiento no ha sido inicializada")
        
        return self.vector_store.similarity_search(query, k=k)