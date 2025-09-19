# app.py

import streamlit as st
from audiorecorder import audiorecorder
from pydub import AudioSegment
import io
import time
import utils
import prompts
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="VocalPrep AI Interview Coach",
    page_icon="🎙️",
    layout="wide"
)

# --- App Title ---
st.markdown("<h1 style='text-align: center;'>VocalPrep: Your AI Interview Coach 🎙️</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Session State Initialization ---
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "interview_domain" not in st.session_state:
    st.session_state.interview_domain = "General"
if "last_played_audio" not in st.session_state:
    st.session_state.last_played_audio = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "final_report" not in st.session_state:
    st.session_state.final_report = ""
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0  # New state to manage audiorecorder key

# --- Helper Functions ---
def autoplay_audio(file_path: str):
    """Function to autoplay audio in Streamlit."""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio controls autoplay="true" style="display:none;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

# --- Sidebar Setup ---
with st.sidebar:
    st.header("Interview Setup")
    st.session_state.interview_domain = st.selectbox(
        "Select Interview Domain:",
        ("General Behavioral", "Python Developer", "Data Scientist", "Machine Learning Engineer", "Frontend Developer")
    )

    if st.button("Start Interview", type="primary"):
        st.session_state.interview_started = True
        st.session_state.chat_history = []
        st.session_state.final_report = ""
        st.session_state.audio_key = 0  # Reset audio key
        # AI starts the conversation
        with st.spinner("Genie is preparing the first question..."):
            initial_prompt = prompts.get_question_prompt(st.session_state.interview_domain, [])
            ai_question = utils.get_llm_response(initial_prompt)
            st.session_state.chat_history.append({"role": "interviewer", "content": ai_question})
        st.rerun()

    if st.session_state.interview_started:
        if st.button("End Interview & Get Report"):
            st.session_state.interview_started = False
            st.session_state.final_report = "This is a placeholder for the final interview report."
            st.session_state.audio_key = 0  # Reset audio key
            st.rerun()

# --- Main Interview Area ---
if not st.session_state.interview_started and not st.session_state.final_report:
    st.info("Setup your interview in the sidebar and click 'Start Interview' to begin.")

elif st.session_state.final_report:
    st.header("📋 Your Interview Report")
    # Display the full chat transcript
    st.subheader("Full Transcript")
    for message in st.session_state.chat_history:
        with st.chat_message("human" if message["role"] == "candidate" else "assistant"):
            st.write(message["content"])
            if "analysis" in message:
                st.info(f"Analysis: {message['analysis']}")

    if st.button("Start a New Interview"):
        st.session_state.final_report = ""
        st.session_state.audio_key = 0  # Reset audio key
        st.rerun()

elif st.session_state.interview_started:
    # Display chat history
    for message in st.session_state.chat_history:
        role = "human" if message["role"] == "candidate" else "assistant"
        with st.chat_message(role):
            st.write(message['content'])
            if message.get("analysis"):
                st.warning(f"🗣️ **Analysis:** {message['analysis']}")

    # Check if it's the user's turn to speak
    if st.session_state.chat_history[-1]["role"] == "interviewer":
        # Play the AI's question audio
        last_question = st.session_state.chat_history[-1]['content']
        if st.session_state.last_played_audio != last_question:
            audio_file = utils.text_to_speech(last_question, "interviewer_question.mp3")
            if audio_file:
                autoplay_audio(audio_file)
                st.session_state.last_played_audio = last_question
                st.session_state.processing = False

        st.subheader("Your Turn to Answer")
        # Use a unique key for the audiorecorder to reset it after each submission
        audio = audiorecorder("Click to record your answer", "Recording...", key=f"audio_{st.session_state.audio_key}")

        # Only process if there is NEW audio AND we are not already processing
        if len(audio) > 0 and not st.session_state.processing:
            # Set the flag to True to prevent reprocessing
            st.session_state.processing = True 
            
            with st.spinner("Transcribing and analyzing your answer..."):
                # Export audio to a format pydub can handle
                audio_segment = AudioSegment.from_file(io.BytesIO(audio.export().read()))
                
                # 1. Transcribe audio
                user_answer_text = utils.transcribe_audio(audio_segment)
                
                # 2. Analyze communication style
                comm_analysis = utils.analyze_communication(audio_segment, user_answer_text)
                wpm = comm_analysis['wpm']
                fillers = comm_analysis['filler_words']
                analysis_str = f"Speaking Pace: {wpm} WPM. Filler Words: {fillers}."

                # Check if this answer is different from the last candidate answer to avoid duplicates
                if not st.session_state.chat_history or st.session_state.chat_history[-1]["role"] != "candidate" or st.session_state.chat_history[-1]["content"] != user_answer_text:
                    st.session_state.chat_history.append({
                        "role": "candidate",
                        "content": user_answer_text,
                        "analysis": analysis_str
                    })

                    # 3. Get AI feedback and next question
                    with st.spinner("Genie is preparing feedback and the next question..."):
                        # Find the last interviewer question dynamically
                        last_question = None
                        for message in reversed(st.session_state.chat_history):
                            if message["role"] == "interviewer":
                                last_question = message["content"]
                                break
                        
                        if last_question is None:
                            # Fallback in case no interviewer question is found
                            last_question = st.session_state.chat_history[-1]["content"]

                        feedback_prompt = prompts.get_feedback_prompt(
                            st.session_state.interview_domain, last_question, user_answer_text
                        )
                        ai_feedback = utils.get_llm_response(feedback_prompt)
                        st.session_state.chat_history.append({"role": "interviewer", "content": ai_feedback})

                        question_prompt = prompts.get_question_prompt(
                            st.session_state.interview_domain, st.session_state.chat_history
                        )
                        ai_next_question = utils.get_llm_response(question_prompt)
                        st.session_state.chat_history.append({"role": "interviewer", "content": ai_next_question})

                # Increment the audio key to reset the audiorecorder widget
                st.session_state.audio_key += 1
                # Reset processing flag after successful processing
                st.session_state.processing = False
                st.rerun()