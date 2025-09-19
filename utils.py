# utils.py

import ollama
import tempfile
import os
from gtts import gTTS
from pydub import AudioSegment
from faster_whisper import WhisperModel
import prompts

# --- Model Initialization ---
# Using a smaller, faster model for real-time transcription
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# --- Core Functions ---

def transcribe_audio(audio_segment):
    """
    Transcribes audio using the faster-whisper model.
    """
    if not audio_segment:
        return "Error: No audio data received."

    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            audio_segment.export(tmp_wav.name, format="wav")
            
            # Transcribe the audio file
            segments, _ = whisper_model.transcribe(tmp_wav.name, beam_size=5)
            
            # Join segments to form the full text
            transcribed_text = " ".join([segment.text for segment in segments])
            
        # Clean up the temporary file
        os.unlink(tmp_wav.name)
        
        return transcribed_text if transcribed_text else "Could not understand the audio. Please speak clearly."
    except Exception as e:
        print(f"Transcription Error: {e}")
        return "An error occurred during transcription."

def get_llm_response(prompt_text):
    """
    Gets a response from the local Ollama model.
    """
    try:
        response = ollama.chat(
            model='llama3.2:latest',
            messages=[{'role': 'user', 'content': prompt_text}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "Sorry, I'm having trouble thinking right now. Please ensure Ollama is running."

def text_to_speech(text, filename="response.mp3"):
    """
    Converts text to an audio file using gTTS.
    Returns the path to the saved audio file.
    """
    try:
        tts = gTTS(text=text, lang='en', tld='com', slow=False)
        file_path = os.path.join("audio_files", filename)
        tts.save(file_path)
        return file_path
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def analyze_communication(audio_segment, transcript):
    """
    Analyzes communication style: speaking pace and filler words.
    """
    if not audio_segment or not transcript:
        return {"wpm": 0, "filler_words": 0}

    duration_seconds = len(audio_segment) / 1000.0
    word_count = len(transcript.split())
    
    # Calculate Words Per Minute (WPM)
    wpm = (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
    
    # Count filler words
    filler_words_list = ['um', 'uh', 'like', 'you know', 'so', 'basically', 'actually']
    filler_word_count = sum(1 for word in transcript.lower().split() if word in filler_words_list)
    
    return {
        "wpm": int(wpm),
        "filler_words": filler_word_count
    }