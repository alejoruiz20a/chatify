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
        
        # AUGMENTATION with history
        prompt = f"""You are a music advisor named Chatify. Your knowledge base will be from a Spotify user with this data:

            {user_profile}

            Relevant information:
            {relevant_info}

            Conversation context:
            {conversation_context}

            Current question: {question}

            Respond in the language the user speaks to you, directly and helpfully, with a cheerful and charismatic touch. Maintain context from previous conversation."""
        
        response = self.llm.invoke(prompt) # GENERATION

        self._add_to_conversation(question, response.content)
        
        return response.content
    
    def _build_conversation_context(self):
        """Builds previous conversation context"""
        if not self.conversation_history:
            return ""
        
        context = "PREVIOUS CONVERSATION CONTEXT:\n"
        # Use only the last 6 messages
        recent_history = self.conversation_history[-6:]
        
        for msg in recent_history:
            if msg["role"] == "user":
                context += f"User: {msg['content']}\n"
            else:
                context += f"Chatify: {msg['content']}\n"
        
        return context + "\n"
    
    def _add_to_conversation(self, question, response):
        """Adds messages to conversation history"""
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if len(self.conversation_history) > 10:  # Maximum 5 exchanges
            self.conversation_history = self.conversation_history[-10:]
    
    def _create_user_profile(self):
        profile = self.music_data

        user_name = profile.get('user_profile', {}).get('display_name', 'User')
        
        all_genres = []
        for artist in profile.get('top_artists', []):
            all_genres.extend(artist.get('genres', []))
        
        genre_counter = Counter(all_genres)
        top_genres = genre_counter.most_common(5)
        
        top_artists = ', '.join([a['name'] for a in profile.get('top_artists', [])[:5]])
        genres = ', '.join([f"{g} ({c})" for g, c in top_genres])

        return f"""Name: {user_name}
            Favorite artists: {top_artists}
            Genres: {genres}"""
    
    def _get_relevant_info(self, question):
        # RETRIEVAL
        results = self.knowledge_base.search(question, k=50)
        
        if not results:
            return "No specific information"
        
        info_text = ""
        for doc in results:
            info_text += f"\n{doc.page_content}\n"
        
        return info_text
    
    def analyze_profile(self):
        user_profile = self._create_user_profile()
        
        prompt = f"""Analyze this music profile:

            {user_profile}

            Provide an analysis that includes:
            - Patterns in musical taste
            - Artists that define their style
            - Suggestions for exploration

            Respond in the language the user speaks to you, directly and helpfully, with a cheerful and charismatic touch."""
        
        print(prompt)
                
        response = self.llm.invoke(prompt)
        return response.content
    
    def clear_conversation_history(self):
        """Clears conversation history"""
        self.conversation_history = []