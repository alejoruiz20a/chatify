import streamlit as st
import os
from dotenv import load_dotenv
from core.music_data_collector import MusicDataCollector
from core.music_knowledge_base import MusicKnowledgeBase
from core.music_advisor import MusicAdvisor
import time

load_dotenv()

st.set_page_config(
    page_title="Chatify",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def initialize_system():
    try:
        with st.status("Inicializando Chatify...", expanded=True) as status:
            status.update(label="Recolectando tu perfil musical...")
            collector = MusicDataCollector()
            music_data = collector.collect_all_data()
            st.session_state.music_data = music_data
            
            status.update(label="Creando base de conocimiento...")
            knowledge_base = MusicKnowledgeBase()
            knowledge_base.initialize_knowledge_base(music_data)
            st.session_state.knowledge_base = knowledge_base

            status.update(label="Guardando datos localmente...")
            collector.save_data_to_file("user_music_data.json")
            
            status.update(label="Configurando tu Chatify...")
            advisor = MusicAdvisor(knowledge_base, music_data)
            st.session_state.advisor = advisor
            
            status.update(label="¡Sistema listo!", state="complete")
        
        st.session_state.data_loaded = True
        st.success("¡Tu Chatify está listo! Puedes empezar a hacer preguntas.")
        
    except Exception as e:
        st.error(f"Error inicializando el sistema: {e}")

with st.sidebar:
    st.title(" Chatify")
    st.markdown("---")
    
    st.subheader("Configuración")
    
    if not st.session_state.data_loaded:
        if st.button("Inicializar Mi Chatify", use_container_width=True, type="primary"):
            initialize_system()
    else:
        st.success("Sistema listo")
        
        if st.session_state.music_data:
            st.subheader("Tu Perfil Musical")
            user_name = st.session_state.music_data['user_profile'].get('display_name', 'Usuario')
            st.write(f"**{user_name}**")
            
            top_artists = st.session_state.music_data.get('top_artists', [])[:3]
            if top_artists:
                st.write("**Artistas Top:**")
                for artist in top_artists:
                    st.write(f"- {artist['name']}")

st.title(" Tu Chatify Personalizado")
st.markdown("Habla con tu asistente de música inteligente que conoce tus gustos y te ayuda a descubrir nueva música.")

if st.session_state.data_loaded:
    col1, = st.columns(1)  
    
    with col1:
        if st.button("Analizar Mi Perfil", use_container_width=True, type="secondary"):
            with st.spinner("Analizando tu perfil musical..."):
                analysis = st.session_state.advisor.analyze_profile()
                st.session_state.messages.append({"role": "user", "content": "Analiza mi perfil musical en detalle"})
                st.session_state.messages.append({"role": "assistant", "content": analysis})
                st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pregúntale algo a tu Chatify..."):
    if not st.session_state.data_loaded:
        st.error("Por favor, inicializa el sistema primero desde la barra lateral.")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(" Tu consejero está pensando..."):
            try:
                response = st.session_state.advisor.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Lo siento, hubo un error: {str(e)}"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
