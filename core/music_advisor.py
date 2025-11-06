from langchain_google_genai import ChatGoogleGenerativeAI
from .spotify_client import SpotifyClient
from collections import Counter
import os

class MusicAdvisor:
    def __init__(self, knowledge_base, music_data):
        self.knowledge_base = knowledge_base
        self.music_data = music_data
        self.spotify_client = SpotifyClient()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5
        )
        
        self.conversation_history = []
    
    def ask(self, question):
        relevant_info = self._get_relevant_info(question)
        user_profile = self._create_user_profile()
        
        conversation_context = self._build_conversation_context()
        
        # AUGMENTATION con historial
        prompt = f"""Eres un consejero musical llamado Chatify. Tu base del conocimiento será la de un usuario de Spotify con estos datos:

            {user_profile}

            Información relevante:
            {relevant_info}

            Contexto de la conversación
            {conversation_context}

            Pregunta actual: {question}

            Responde en el idioma que te hable el usuario, de forma directa y útil, con un toque alegre y carismático. Mantén el contexto de la conversación anterior."""
        
        response = self.llm.invoke(prompt) # GENERATION

        self._add_to_conversation(question, response.content)
        
        return response.content
    
    def _build_conversation_context(self):
        """Construye el contexto de conversación anterior"""
        if not self.conversation_history:
            return ""
        
        context = "CONTEXTO DE CONVERSACIÓN ANTERIOR:\n"
        # Usar solo los últimos 6 mensajes 
        recent_history = self.conversation_history[-6:]
        
        for msg in recent_history:
            if msg["role"] == "user":
                context += f"Usuario: {msg['content']}\n"
            else:
                context += f"Chatify: {msg['content']}\n"
        
        return context + "\n"
    
    def _add_to_conversation(self, question, response):
        """Añade mensajes al historial de conversación"""
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if len(self.conversation_history) > 10:  # Máximo 5 intercambios
            self.conversation_history = self.conversation_history[-10:]
    
    def _create_user_profile(self):
        profile = self.music_data

        user_name = profile.get('user_profile', {}).get('display_name', 'Usuario')
        
        all_genres = []
        for artist in profile.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(5)
        
        top_artists = ', '.join([a['name'] for a in profile.get('top_artists', [])[:5]])
        genres = ', '.join([f"{g} ({c})" for g, c in top_genres])
        
        top_tracks = ', '.join([t['name'] for t in profile.get('top_tracks', [])[:5]])

        return f"""Nombre: {user_name}
            Artistas favoritos: {top_artists}
            Géneros: {genres}
            Canciones más escuchadas: {top_tracks}
            Canciones guardadas: {len(profile.get('saved_tracks', []))}"""
    
    def _get_relevant_info(self, question):
        # RETRIEVAL
        results = self.knowledge_base.search(question, k=20)
        
        if not results:
            return "Sin información específica"
        
        info_text = ""
        for doc in results:
            info_text += f"\n{doc.page_content}\n"
        
        return info_text
    
    def analyze_profile(self):
        user_profile = self._create_user_profile()
        
        prompt = f"""Analiza este perfil musical:

            {user_profile}

            Proporciona un análisis que incluya:
            - Patrones en gustos musicales
            - Artistas que definen su estilo
            - Sugerencias para explorar

            Responde en el idioma que te hable el usuario, de forma directa y útil, con un toque alegre y carismático."""
        
        print(prompt)
                
        response = self.llm.invoke(prompt)
        return response.content
    
    def clear_conversation_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
    
    # def get_recommendations(self):
    #     top_artists = self.music_data.get('top_artists', [])[:3]
    #     if not top_artists:
    #         return "No hay suficientes datos para recomendaciones"
        
    #     artist_ids = [artist['id'] for artist in top_artists[:2]]
    #     recommendations = self.spotify_client.get_recommendations(seed_artists=artist_ids, limit=8)
        
    #     if not recommendations or 'tracks' not in recommendations:
    #         return "No se pudieron generar recomendaciones"
        
    #     user_profile = self._create_user_profile()
    #     tracks_info = self._format_recommendations(recommendations)
        
    #     prompt = f"""Basado en este perfil:
    #         {user_profile}

    #         Spotify recomienda:
    #         {tracks_info}

    #         Presenta estas recomendaciones de forma clara y explica brevemente por qué podrían gustarle."""
        
    #     response = self.llm.invoke(prompt)
    #     return response.content
    
    # def _format_recommendations(self, recommendations):
    #     formatted = ""
    #     for i, track in enumerate(recommendations['tracks'], 1):
    #         artists = ", ".join([a['name'] for a in track['artists']])
    #         formatted += f"{i}. {track['name']} - {artists}\n"
    #     return formatted