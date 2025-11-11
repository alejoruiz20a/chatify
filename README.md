# Chatify - Your Personal Music Advisor

![Chatify](https://img.shields.io/badge/Chatify-Music%20Advisor-1DB954?style=for-the-badge&logo=spotify&logoColor=white)

## What is Chatify?

Chatify is your intelligent music companion that analyzes your Spotify listening habits and helps you discover new music, understand your musical taste, and have meaningful conversations about your favorite artists and songs.

Imagine having a music expert who knows everything about your taste and can recommend new discoveries just for you - that's Chatify!

## Features

- **Personalized Music Analysis** - Get insights about your listening patterns
- **AI-Powered Conversations** - Chat naturally about your music taste
- **Smart Recommendations** - Discover new artists and songs you'll love
- **Taste Profiling** - Understand your musical preferences in depth
- **Persistent Memory** - Remembers your preferences across sessions

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/alejoruiz20a/chatify.git
cd chatify
```

### 2. Set Up Environment

Create a .env file in the project root with your API keys:

```env
# Google Gemini AI Key (Required)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Weaviate Vector Database (Required)
WEAVIATE_URL=your_weaviate_cluster_url
WEAVIATE_API_KEY=your_weaviate_api_key

# Spotify Developer Keys (only required for development)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## How to Use Chatify

### First Time Setup

1. Click "Sign in with Spotify" - Grant Chatify access to your music data
2. Initialize Your Profile - Click "Initialize My Chatify" in the sidebar
3. Start Chatting! - Ask questions about your music taste

### Example Questions to Ask

- "What are my top music genres?"
- "Recommend new artists based on my taste"
- "Analyze my listening patterns"
- "What similar artists would I like?"
- "Tell me about my favorite music style"

## Project Structure

```
chatify/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (you create this)
├── core/
│   ├── auth_manager.py   # Spotify authentication
│   ├── music_advisor.py  # AI conversation handler
│   ├── music_data_collector.py  # Spotify data collection
│   └── music_knowledge_base.py  # Vector database management
|   └── spotify_client.py
```

## Contributing

We welcome contributions! Feel free to submit issues and enhancement requests.

**Happy listening!**
