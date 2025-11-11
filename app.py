import streamlit as st
import os
from dotenv import load_dotenv
from core.music_data_collector import MusicDataCollector
from core.music_knowledge_base import MusicKnowledgeBase
from core.music_advisor import MusicAdvisor
from core.auth_manager import AuthManager
import time

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
                with open("user_token.json", "w") as f:
                    json.dump(token_info, f)
            except Exception as e:
                pass

            st.query_params.clear()
            st.rerun()

# Handle authentication callback
handle_auth_callback()

# NOW load token from file ONLY if not already authenticated
if not st.session_state.authenticated and st.session_state.token_info is None:
    try:
        import json
        import os
        if os.path.exists("user_token.json"):
            with open("user_token.json", "r") as f:
                st.session_state.token_info = json.load(f)
                st.session_state.authenticated = True
                # Optional: small rerun to refresh the state
                st.rerun()
    except FileNotFoundError:
        pass  # No saved token, stay logged out
    except Exception as e:
        st.sidebar.error(f"Error loading saved token: {e}")
        # If token is corrupted, delete it
        try:
            os.remove("user_token.json")
        except:
            pass

def initialize_system():
    """Initializes system with authenticated user data"""
    try:
        with st.status("Initializing Chatify...", expanded=True) as status:
            status.update(label="Collecting your music profile...")
            collector = MusicDataCollector(st.session_state.token_info)
            music_data = collector.collect_all_data()
            st.session_state.music_data = music_data
            
            # Get user ID for multi-tenancy
            user_id = music_data.get('user_profile', {}).get('id', 'unknown_user')
            
            status.update(label="Creating knowledge base...")
            knowledge_base = MusicKnowledgeBase(user_id=user_id)
            knowledge_base.initialize_knowledge_base(music_data)
            st.session_state.knowledge_base = knowledge_base

            status.update(label="Saving data locally...")
            collector.save_data_to_file("user_music_data.json")
            
            status.update(label="Setting up your Chatify...")
            # 👇 Pasa el token_info al MusicAdvisor
            advisor = MusicAdvisor(knowledge_base, music_data, st.session_state.token_info)
            st.session_state.advisor = advisor
            
            status.update(label="System ready!", state="complete")
        
        st.session_state.data_loaded = True
        st.success("Your Chatify is ready! You can start asking questions.")
        
    except Exception as e:
        st.error(f"Error initializing system: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def logout():
    """Logs out the user and clears all session data"""
    # Remove token file first
    try:
        import os
        if os.path.exists("user_token.json"):
            os.remove("user_token.json")
    except Exception as e:
        print(f"Error removing token file: {e}")
    
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
            <button style="
                background-color: #1DB954;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border: none;
                border-radius: 50px;
                font-weight: bold;
                width: 100%;
            ">
                Sign in with Spotify
            </button>
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("Your data is secure. We only access read-only information from your music profile.")

else:
    # Authenticated user - Main interface
    with st.sidebar:
        st.title("Chatify")
        st.markdown("---")
        
        st.subheader("Settings")
        
        if not st.session_state.data_loaded:
            if st.button("Initialize My Chatify", use_container_width=True, type="primary"):
                initialize_system()
        else:
            st.success("System ready")
            
            if st.session_state.music_data:
                st.subheader("Your Music Profile")
                user_name = st.session_state.music_data['user_profile'].get('display_name', 'User')
                st.write(f"**{user_name}**")
                
                top_artists = st.session_state.music_data.get('top_artists', [])[:3]
                if top_artists:
                    st.write("**Top Artists:**")
                    for artist in top_artists:
                        st.write(f"- {artist['name']}")
        
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
            st.error("Please initialize the system first from the sidebar.")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Your advisor is thinking..."):
                try:
                    response = st.session_state.advisor.ask(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, there was an error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})