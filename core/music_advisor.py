from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .knowledge_base import MusicKnowledgeBase
from .spotify_client import SpotifyClient
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

class MusicAdvisor:
    def __init__(self, knowledge_base: MusicKnowledgeBase, music_data: dict):
        self.knowledge_base = knowledge_base
        self.music_data = music_data
        self.spotify_client = SpotifyClient()
        
        # Configurar Gemini con la versión compatible
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5
        )
    
    def ask(self, question: str) -> str:
        """Responde preguntas sobre música usando el perfil del usuario"""
        try:
            # Obtener información relevante
            relevant_info = self._get_relevant_info(question)
            user_profile = self._create_user_profile()
            
            # Construir prompt
            prompt = self._build_prompt(user_profile, relevant_info, question)
            
            # Obtener respuesta
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _build_prompt(self, user_profile: str, relevant_info: str, question: str) -> str:
        """Construye el prompt para el LLM"""
        return f"""Eres un consejero musical personalizado y entusiasta. Tu usuario tiene los siguientes gustos musicales:

PERFIL MUSICAL DEL USUARIO:
{user_profile}

INFORMACIÓN RELEVANTE DE SU BIBLIOTECA:
{relevant_info}

Responde la siguiente pregunta del usuario de manera útil, personalizada y apasionada. 
Usa emojis musicales para hacerlo más amigable. Sé específico basándote en su perfil único.

PREGUNTA: {question}

Responde en español de forma conversacional pero informativa. Muestra entusiasmo por la música!

RESPUESTA:"""
    
    def _create_user_profile(self) -> str:
        """Crea un resumen del perfil musical del usuario"""
        profile = self.music_data
        
        all_genres = []
        for artist in profile.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(5)
        
        top_artists = profile.get('top_artists', [])[:8]
        top_tracks = profile.get('top_tracks', [])[:5]
        
        profile_text = f"""**PERFIL MUSICAL**

**Artistas Favoritos:**
{', '.join([artist['name'] for artist in top_artists])}

**Géneros Principales:**
{', '.join([f"{genre} ({count})" for genre, count in top_genres])}

**Canciones Destacadas:**
{', '.join([track['name'] for track in top_tracks])}

**Estadísticas:**
- {len(profile.get('saved_tracks', []))} canciones guardadas
- {len(profile.get('playlists', []))} playlists creadas
- {len(profile.get('artists_info', {}))} artistas en biblioteca
"""
        return profile_text
    
    def _get_relevant_info(self, question: str) -> str:
        """Obtiene información relevante de la base de conocimiento"""
        try:
            results = self.knowledge_base.search(question, k=4)
            
            if not results:
                return "No se encontró información específica en la base de conocimiento para esta pregunta."
            
            info_text = "INFORMACIÓN ENCONTRADA EN SU BIBLIOTECA:\n"
            for i, doc in enumerate(results, 1):
                doc_type = doc.metadata.get('type', 'info')
                info_text += f"\n--- {doc_type.upper()} ---\n"
                info_text += f"{doc.page_content}\n"
            
            return info_text
            
        except Exception as e:
            return f"Error buscando información: {e}"
    
    def get_recommendations(self) -> str:
        """Obtiene recomendaciones musicales personalizadas"""
        try:
            top_artists = self.music_data.get('top_artists', [])[:3]
            if not top_artists:
                return "No hay suficientes artistas en tu perfil para hacer recomendaciones."
            
            artist_names = [artist['name'] for artist in top_artists]
            artist_ids = [artist['id'] for artist in top_artists[:2]]
            
            recommendations = self.spotify_client.get_recommendations(
                seed_artists=artist_ids,
                limit=8
            )
            
            if not recommendations or 'tracks' not in recommendations:
                return "No se pudieron generar recomendaciones en este momento."
            
            # Usar LLM para formatear recomendaciones
            user_profile = self._create_user_profile()
            prompt = f"""Basándote en este perfil musical:

            {user_profile}

            Genera recomendaciones musicales personalizadas. El usuario ama estos artistas: {', '.join(artist_names)}

            Aquí tienes recomendaciones técnicas de Spotify. Por favor, organízalas de forma amigable y explica por qué le podrían gustar:

            RECOMENDACIONES TÉCNICAS:
            {self._format_spotify_recommendations(recommendations)}

            Responde con entusiasmo, organiza las recomendaciones de forma clara y explica brevemente por qué cada canción podría gustarle basándote en sus gustos."""
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"Error obteniendo recomendaciones: {e}"
    
    def _format_spotify_recommendations(self, recommendations: dict) -> str:
        """Formatea las recomendaciones de Spotify para el prompt"""
        formatted = ""
        for i, track in enumerate(recommendations['tracks'], 1):
            artists = ", ".join([artist['name'] for artist in track['artists']])
            formatted += f"{i}. {track['name']} - {artists}\n"
            formatted += f"   Álbum: {track['album']['name']}\n"
            formatted += f"   Popularidad: {track.get('popularity', 'N/A')}/100\n\n"
        return formatted
    
    def analyze_profile(self) -> str:
        """Proporciona un análisis detallado del perfil musical"""
        try:
            user_profile = self._create_user_profile()
            
            prompt = f"""Analiza este perfil musical y proporciona insights interesantes:

{user_profile}

Proporciona un análisis detallado que incluya:
- Patrones en sus gustos musicales
- Combinaciones interesantes de géneros
- Artistas que definen su estilo
- Sugerencias para explorar basadas en sus preferencias

Sé detallado pero conversacional. Usa emojis y muestra entusiasmo! 🎵"""
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"Error analizando perfil: {e}"