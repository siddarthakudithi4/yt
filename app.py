import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from pytube import YouTube
from gtts import gTTS
import os
import tempfile
import requests
from io import BytesIO
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Language code mapping with Indian languages
LANGUAGE_CODES = {
    'english': 'en',
    'telugu': 'te',
    'tamil': 'ta',
    'hindi': 'hi',
    'kannada': 'kn',
    'malayalam': 'ml',
    'bengali': 'bn',
    'marathi': 'mr',
    'gujarati': 'gu',
    'punjabi': 'pa',
    'urdu': 'ur',
    'తెలుగు': 'te',
    'தமிழ்': 'ta',
    'हिन्दी': 'hi',
    'ಕನ್ನಡ': 'kn',
    'മലയാളം': 'ml',
    'বাংলা': 'bn',
    'मराठी': 'mr',
    'ગુજરાતી': 'gu',
    'ਪੰਜਾਬੀ': 'pa',
    'اردو': 'ur'
}

def extract_transcript(video_url):
    try:
        video_id = YouTube(video_url).video_id
        try:
            # Try to get existing captions
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except:
            st.error("No captions available. Please try a different video.")
            return None
            
    except Exception as e:
        st.error(f"Error extracting transcript: {str(e)}")
        return None

def translate_text(text, target_language):
    try:
        llm = ChatGroq(
            temperature=0.1,
            model_name="mixtral-8x7b-32768",
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        messages = [
            SystemMessage(content=f"""
                Translate the text to {target_language}. 
                Maintain original formatting and punctuation.
                Preserve technical terms in their original form.
                Use correct regional script.
            """),
            HumanMessage(content=text)
        ]
        return llm(messages).content
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return None

def text_to_speech(text, language):
    try:
        lang_code = LANGUAGE_CODES.get(language.lower().strip(), None)
        if not lang_code:
            lang_code = next((v for k, v in LANGUAGE_CODES.items() 
                            if k.strip().lower() == language.lower().strip()), None)
        
        if not lang_code:
            st.error(f"Language '{language}' not supported")
            return None
            
        # Use Google's Indian domain for regional languages
        tld = 'co.in' if lang_code in ['te', 'ta', 'hi', 'kn', 'ml'] else 'com'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts = gTTS(
                text=text, 
                lang=lang_code, 
                tld=tld, 
                slow=False
            )
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

def main():
    st.title("YouTube Translator 🇮🇳 (No FFmpeg)")
    
    # Initialize session state
    if 'translated_text' not in st.session_state:
        st.session_state.translated_text = None
    
    video_url = st.text_input("Enter YouTube Video URL:")
    target_language = st.text_input("Enter Target Language (e.g., 'Telugu', 'తెలుగు'):")
    
    if st.button("Translate Transcript"):
        if video_url and target_language:
            with st.spinner("Processing..."):
                start_time = time.time()
                
                # Extract transcript
                transcript = extract_transcript(video_url)
                
                # Translate text
                if transcript:
                    st.session_state.translated_text = translate_text(transcript, target_language)
                    
                st.write(f"Processing time: {time.time() - start_time:.2f}s")
        else:
            st.warning("Please provide both URL and language")

    if st.session_state.translated_text:
        st.subheader("Translated Text")
        st.write(st.session_state.translated_text)
        
        if st.button("Convert to Speech 🔊"):
            with st.spinner("Generating audio..."):
                audio_file = text_to_speech(
                    st.session_state.translated_text,
                    target_language
                )
                if audio_file:
                    st.audio(audio_file)
                    os.unlink(audio_file)

if __name__ == "__main__":
    main()