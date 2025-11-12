import streamlit as st
import os
from dotenv import load_dotenv
from core.music_data_collector import MusicDataCollector
from core.music_knowledge_base import MusicKnowledgeBase
from core.music_advisor import MusicAdvisor
from core.auth_manager import AuthManager

load_dotenv()

st.set_page_config(
    page_title="Chatify",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session states
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token_info" not in st.session_state:
    st.session_state.token_info = None
if "music_data" not in st.session_state:
    st.session_state.music_data = None
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = None
if "advisor" not in st.session_state:
    st.session_state.advisor = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "initializing" not in st.session_state:
    st.session_state.initializing = False

# Initialize authentication manager
auth_manager = AuthManager()

def handle_auth_callback():
    """Handles Spotify authentication callback"""
    query_params = st.query_params
    
    if "code" in query_params:
        code = query_params["code"]
        token_info = auth_manager.get_access_token(code)
        
        if token_info:
            st.session_state.token_info = token_info
            st.session_state.authenticated = True
            
            try:
                import json
                with open("user_token.json", "w", encoding='utf-8') as f:
                    json.dump(token_info, f)
            except Exception as e:
                pass

            st.query_params.clear()
            st.rerun()

# Handle authentication callback
handle_auth_callback()

# Load token from file if not already authenticated
if not st.session_state.authenticated and st.session_state.token_info is None:
    try:
        import json
        import os
        if os.path.exists("user_token.json"):
            with open("user_token.json", "r", encoding='utf-8') as f:
                st.session_state.token_info = json.load(f)
                st.session_state.authenticated = True
                st.rerun()
    except FileNotFoundError:
        pass
    except Exception as e:
        st.sidebar.error(f"Error loading saved token: {e}")
        try:
            os.remove("user_token.json")
        except:
            pass

def initialize_system():
    """Initializes system with authenticated user data"""
    try:
        with st.status("Initializing Chatify...", expanded=True) as status:
            # First, get user ID quickly (single API call)
            status.update(label="Checking your profile...")
            user_id = auth_manager.get_user_id(st.session_state.token_info)
            print(f"User ID: {user_id}")  # Debug
            
            # Check if knowledge base already exists for this user
            status.update(label="Checking knowledge base...")
            knowledge_base = MusicKnowledgeBase(user_id=user_id)
            
            # Check if collection exists (uses cache, very fast)
            if knowledge_base.collection_exists():
                status.update(label="Knowledge base found! Loading your data...")
                # Collection exists, try to load existing data from file
                try:
                    import json
                    if os.path.exists("user_music_data.json"):
                        with open("user_music_data.json", "r", encoding='utf-8') as f:
                            music_data = json.load(f)
                            # Verify it's the same user
                            if music_data.get('user_profile', {}).get('id') == user_id:
                                st.session_state.music_data = music_data
                                status.update(label="Data loaded from cache!")
                            else:
                                # Different user, need to collect fresh data
                                raise FileNotFoundError("User mismatch")
                    else:
                        raise FileNotFoundError("No cached data")
                except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
                    # No cached data, different user, or encoding error - collect fresh data
                    status.update(label="Collecting your music profile...")
                    collector = MusicDataCollector(st.session_state.token_info)
                    music_data = collector.collect_all_data()
                    st.session_state.music_data = music_data
                    collector.save_data_to_file("user_music_data.json")
            else:
                # Collection doesn't exist, need to collect all data
                status.update(label="Collecting your music profile...")
                collector = MusicDataCollector(st.session_state.token_info)
                music_data = collector.collect_all_data()
                st.session_state.music_data = music_data
                
                status.update(label="Creating knowledge base...")
                knowledge_base.initialize_knowledge_base(music_data, force_recreate=False)
                
                status.update(label="Saving data locally...")
                collector.save_data_to_file("user_music_data.json")
            
            st.session_state.knowledge_base = knowledge_base
            
            status.update(label="Setting up your Chatify...")
            advisor = MusicAdvisor(knowledge_base, st.session_state.music_data, st.session_state.token_info)
            st.session_state.advisor = advisor
            
            status.update(label="System ready!", state="complete")
        
        st.session_state.data_loaded = True
        st.success("Your Chatify is ready! You can start asking questions.")
        
    except Exception as e:
        st.session_state.initializing = False
        st.error(f"Error initializing system: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def update_knowledge_base():
    """Updates the knowledge base with fresh data"""
    try:
        with st.status("Updating Knowledge Base...", expanded=True) as status:
            status.update(label="Collecting fresh music data...")
            collector = MusicDataCollector(st.session_state.token_info)
            music_data = collector.collect_all_data()
            st.session_state.music_data = music_data
            
            status.update(label="Updating knowledge base...")
            st.session_state.knowledge_base.update_knowledge_base(music_data)
            
            status.update(label="Refreshing advisor...")
            st.session_state.advisor = MusicAdvisor(
                st.session_state.knowledge_base, 
                music_data, 
                st.session_state.token_info
            )
            
            status.update(label="Knowledge base updated!", state="complete")
        
        st.success("Your knowledge base has been updated with the latest data!")
        
    except Exception as e:
        st.error(f"Error updating knowledge base: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def logout():
    """Logs out the user and clears all session data"""
    try:
        import os
        if os.path.exists("user_token.json"):
            os.remove("user_token.json")
    except Exception as e:
        print(f"Error removing token file: {e}")
    
    # Close Weaviate connection if exists
    if st.session_state.knowledge_base:
        try:
            st.session_state.knowledge_base.close()
        except:
            pass
    
    # Clear ALL session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize basic session states
    st.session_state.authenticated = False
    st.session_state.token_info = None
    st.session_state.music_data = None
    st.session_state.knowledge_base = None
    st.session_state.advisor = None
    st.session_state.messages = []
    st.session_state.data_loaded = False
    st.session_state.initializing = False
    
    st.rerun()

# Login screen
if not st.session_state.authenticated:
    st.title("Welcome to Chatify")
    st.markdown("""
    ### Your intelligent personal music assistant
    
    Chatify analyzes your Spotify profile and helps you:
    - Discover new music based on your taste
    - Understand your musical patterns
    - Chat about your favorite artists and songs
    - Get personalized recommendations
    
    ---
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("**Sign in with your Spotify account to get started**")
        
        auth_url = auth_manager.get_auth_url()

        st.markdown(f"""
        <a href="{auth_url}" target="_self">
            <button style="background-color: #1DB954; color: white; padding: 15px 32px; border: none; border-radius: 50px; font-weight: bold; width: 100%;">
                Sign in with Spotify
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("Your data is secure. We only access read-only information from your music profile.")

else:
    # Authenticated user - Main interface
    # Auto-initialize system if not already loaded
    if not st.session_state.data_loaded and not st.session_state.initializing:
        st.session_state.initializing = True
        initialize_system()
        st.session_state.initializing = False
        st.rerun()
    
    with st.sidebar:
        st.title("Chatify")
        st.markdown("---")
        
        st.subheader("Settings")
        
        if st.session_state.data_loaded:
            st.success("System ready")
            
            if st.session_state.music_data:
                st.subheader("Your Music Profile")
                user_name = st.session_state.music_data['user_profile'].get('display_name', 'User')
                user_id = st.session_state.music_data['user_profile'].get('id', 'unknown')
                st.write(f"**{user_name}**")
                
                top_artists = st.session_state.music_data.get('top_artists', [])[:3]
                if top_artists:
                    st.write("**Top Artists:**")
                    for artist in top_artists:
                        st.write(f"- {artist['name']}")
            
            st.markdown("---")
            st.subheader("Data Management")
            
            if st.button("Update Knowledge Base", use_container_width=True, type="secondary"):
                update_knowledge_base()
                st.rerun()
        
        st.markdown("---")
        if st.button("Sign Out", use_container_width=True, type="secondary"):
            logout()

    st.title("Your Personalized Chatify")
    st.markdown("Chat with your intelligent music assistant that knows your taste and helps you discover new music.")

    if st.session_state.data_loaded:
        col1, = st.columns(1)  
        
        with col1:
            if st.button("Analyze My Profile", use_container_width=True, type="secondary"):
                with st.spinner("Analyzing your music profile..."):
                    analysis = st.session_state.advisor.analyze_profile()
                    st.session_state.messages.append({"role": "user", "content": "Analyze my music profile in detail"})
                    st.session_state.messages.append({"role": "assistant", "content": analysis})
                    st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask your Chatify something..."):
        if not st.session_state.data_loaded:
            st.error("System is initializing, please wait...")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Your advisor is thinking..."):
                try:
                    response = st.session_state.advisor.ask(prompt)
                    # Update session state in case music_data was updated during auto-initialization
                    if st.session_state.advisor.music_data:
                        st.session_state.music_data = st.session_state.advisor.music_data
                    if st.session_state.advisor.knowledge_base:
                        st.session_state.knowledge_base = st.session_state.advisor.knowledge_base
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, there was an error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})