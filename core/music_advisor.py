from langchain_google_genai import ChatGoogleGenerativeAI
from .spotify_client import SpotifyClient
from .music_data_collector import MusicDataCollector
from collections import Counter
import os

class MusicAdvisor:
    def __init__(self, knowledge_base, music_data, token_info=None):
        self.knowledge_base = knowledge_base
        self.music_data = music_data
        self.token_info = token_info
        
        # Initialize SpotifyClient with token_info
        if token_info:
            self.spotify_client = SpotifyClient(token_info)
        else:
            self.spotify_client = None  # Or handle this case as needed
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4
        )
        
        self.conversation_history = []
    
    def ask(self, question):
        # If we need to use Spotify API in responses, check if client is available
        if not self.spotify_client:
            # You can choose to skip Spotify functionality or handle differently
            pass
            
        relevant_info = self._get_relevant_info(question)
        user_profile = self._create_user_profile()
        
        conversation_context = self._build_conversation_context()
        
        prompt = f"""You are a music advisor named Chatify. Your knowledge base will be from a Spotify user with this data:

{user_profile}

Relevant information:
{relevant_info}

Conversation context:
{conversation_context}

Current question: {question}

Respond in the language the user speaks to you, directly and helpfully, with a cheerful and charismatic touch. Maintain context from previous conversation.

Note: If the knowledge base was just auto-initialized, acknowledge this to the user in a friendly way.
"""
        
        response = self.llm.invoke(prompt)
        
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
        
        genres = ', '.join([f"{g} ({c})" for g, c in top_genres])

        return f"""Name: {user_name}
            Genres: {genres}"""
    
    def _get_relevant_info(self, question):
        # RETRIEVAL
        try:
            results = self.knowledge_base.search(question, k=50)
            
            if not results:
                return "No specific information"
            
            info_text = ""
            for doc in results:
                info_text += f"\n{doc.page_content}\n"
            
            return info_text
        except ValueError as e:
            if "KNOWLEDGE_BASE_NEEDS_UPDATE" in str(e):
                # Try to auto-initialize the knowledge base
                if self._auto_initialize_knowledge_base():
                    # Retry the search after initialization
                    try:
                        results = self.knowledge_base.search(question, k=50)
                        if not results:
                            return "No specific information"
                        info_text = ""
                        for doc in results:
                            info_text += f"\n{doc.page_content}\n"
                        return info_text
                    except Exception as retry_error:
                        return f"ERROR: Knowledge base was recreated but search still failed: {str(retry_error)}"
                else:
                    return "ERROR: Knowledge base collection not found and could not be auto-initialized. Please try updating your Knowledge Base manually."
        except Exception as e:
            # For other errors, return a generic message
            return f"ERROR: Unable to access knowledge base: {str(e)}"
    
    def _auto_initialize_knowledge_base(self):
        """Automatically initialize the knowledge base when it's missing"""
        try:
            if not self.token_info:
                print("No token info available for auto-initialization")
                return False
            
            # Get user ID from existing music data or fetch it
            user_id = self.music_data.get('user_profile', {}).get('id') if self.music_data else None
            
            if not user_id:
                # Need to get user ID first
                from .music_data_collector import MusicDataCollector
                collector = MusicDataCollector(self.token_info)
                user_id = collector.get_user_id()
                if user_id == 'unknown_user':
                    print("Could not get user ID for auto-initialization")
                    return False
            
            # Check if we have music data, if not, collect it
            if not self.music_data or not self.music_data.get('user_profile'):
                print("Collecting music data for auto-initialization...")
                collector = MusicDataCollector(self.token_info)
                self.music_data = collector.collect_all_data()
            
            # Initialize the knowledge base
            print(f"Auto-initializing knowledge base for user {user_id}...")
            
            # Update user_id and collection_name BEFORE checking/creating
            self.knowledge_base.user_id = user_id
            self.knowledge_base.collection_name = f"MusicProfile_{user_id.replace('-', '_')}"
            
            # Clear any stale cache for this collection
            self.knowledge_base._clear_cache()
            
            print(f"Collection name: {self.knowledge_base.collection_name}")
            print(f"Checking if collection exists (without cache)...")
            
            # Check without cache first to see if collection really exists
            client = self.knowledge_base._get_weaviate_client()
            collection_exists = client.collections.exists(self.knowledge_base.collection_name)
            
            if not collection_exists:
                print(f"Collection does not exist, creating it...")
                # Create the collection directly
                self.knowledge_base._create_collection(client)
                
                # Create documents and add them
                documents = self.knowledge_base._create_documents(self.music_data)
                self.knowledge_base._add_documents_to_collection(client, documents)
                
                # Update cache after successful creation
                self.knowledge_base._update_cache()
                print("Knowledge base auto-initialized successfully!")
            else:
                print(f"Collection already exists, verifying it's properly set up...")
                # Even if it exists, make sure it has the right data
                # For now, just update cache
                self.knowledge_base._update_cache()
            
            return True
        except Exception as e:
            print(f"Error auto-initializing knowledge base: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
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