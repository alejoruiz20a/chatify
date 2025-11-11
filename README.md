# 🎵 Chatify - Your Personal Music Advisor

![Chatify](https://img.shields.io/badge/Chatify-Music%20Advisor-1DB954?style=for-the-badge&logo=spotify&logoColor=white)

## 🌟 What is Chatify?

Chatify is your intelligent music companion that analyzes your Spotify listening habits and helps you discover new music, understand your musical taste, and have meaningful conversations about your favorite artists and songs.

Imagine having a music expert who knows everything about your taste and can recommend new discoveries just for you - that's Chatify!

## ✨ Features

- **🎧 Personalized Music Analysis** - Get insights about your listening patterns
- **🤖 AI-Powered Conversations** - Chat naturally about your music taste
- **🔍 Smart Recommendations** - Discover new artists and songs you'll love
- **📊 Taste Profiling** - Understand your musical preferences in depth
- **💾 Persistent Memory** - Remembers your preferences across sessions

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/chatify.git
cd chatify
```

### 2. Set Up Environment

Create a .env file in the project root with your API keys:

```env
# Spotify Developer Keys (Required)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8501

# Google Gemini AI Key (Required)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Weaviate Vector Database (Required)
WEAVIATE_URL=your_weaviate_cluster_url
WEAVIATE_API_KEY=your_weaviate_api_key
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

## 🔑 Getting Your API Keys

### Spotify Developer Account

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the Client ID and Client Secret to your .env file
4. Add http://localhost:8501 as a redirect URI in your app settings

### Google Gemini AI

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy it to your .env file as GOOGLE_API_KEY

### Weaviate Database

1. Sign up at [Weaviate Cloud](https://console.weaviate.cloud/)
2. Create a new cluster
3. Get your cluster URL and API key
4. Add them to your .env file

## 🎯 How to Use Chatify

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

## 🛠️ Technical Details

Chatify uses advanced AI technology to understand your music preferences:

- **Spotify Integration** - Securely accesses your listening history and saved music
- **Vector Database** - Stores and retrieves your music data efficiently
- **Google Gemini AI** - Powers natural conversations and insights
- **Streamlit** - Provides the beautiful web interface

## 🔒 Privacy & Security

- Your Spotify data is read-only and never stored permanently
- All conversations are private and processed securely
- You can logout at any time to clear all your data
- No personal information is shared with third parties

## ❓ Frequently Asked Questions

**Is my Spotify data safe?**  
Yes! Chatify only requests read-only access to your Spotify data and doesn't modify anything in your account.

**Do I need to pay for any services?**  
The basic version is free, but you'll need your own API keys for Spotify, Google Gemini, and Weaviate.

**Can I use Chatify without technical knowledge?**  
Absolutely! Just follow the setup steps above - no coding required.

**What if I get an error during setup?**  
Check that all your API keys in the .env file are correct and that you've installed all requirements.

## 🐛 Troubleshooting

**Common Issues**

- "Error initializing system"  
  - Check that all API keys in .env are correct  
  - Verify your Spotify app has the correct redirect URI

- "Cannot connect to Spotify"  
  - Ensure your Spotify Developer app is set to "Development" mode  
  - Check your internet connection

- "Module not found errors"  
  - Run `pip install -r requirements.txt` again  
  - Make sure you're in the correct project directory

## 📁 Project Structure

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
└── user_token.json       # Auto-generated session file
```

## 🤝 Contributing

We welcome contributions! Feel free to submit issues and enhancement requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Ready to discover your next favorite song? 🎶

Start Chatify and let the music journey begin!  
If you have any questions, check the troubleshooting section or create an issue in the repository.

**Happy listening! 🎵**
