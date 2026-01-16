import streamlit as st
from google import genai
import os
from dotenv import load_dotenv
import base64
import json
from datetime import datetime
from pathlib import Path
from audio_recorder_streamlit import audio_recorder

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="LectureLift",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE PERSISTENCE ---
DB_PATH = Path("lecture_history.json")

def load_db():
    if DB_PATH.exists():
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return {"history": []}

def save_to_db(entry):
    db = load_db()
    db["history"].append(entry)
    with open(DB_PATH, 'w') as f:
        json.dump(db, f)

# Initialize Session States
if 'upload_data' not in st.session_state:
    st.session_state.upload_data = {"notes": None, "quiz": None, "topics": None}
if 'record_data' not in st.session_state:
    st.session_state.record_data = {"notes": None, "quiz": None, "topics": None, "transcription": None}
# NEW: Session state to track which history item is being viewed
if 'selected_history' not in st.session_state:
    st.session_state.selected_history = None

# --- MAIN TITLE SECTION ---
st.markdown("""
    <div style="text-align: center; padding: 2rem 0rem;">
        <h1 style="
            font-size: 5rem; 
            font-weight: 800; 
            background: linear-gradient(135deg, #38bdf8 0%, #588a99 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0px 10px 30px rgba(56, 189, 248, 0.4);
            margin-bottom: 0px;
        ">
            LectureLift
        </h1>
        <p style="color: #588a99; font-size: 1.2rem; letter-spacing: 2px; text-transform: uppercase;">
            Transform your lectures into comprehensive study materials
        </p>
    </div>
""", unsafe_allow_html=True)

# --- ULTIMATE GLOW THEME CSS ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }

    /* Sidebar Glow & Modern Styling */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid rgba(56, 189, 248, 0.3);
        box-shadow: 10px 0px 30px -15px rgba(56, 189, 248, 0.4);
    }

    /* Sidebar Title */
    .sidebar-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8 0%, #588a99 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }

    /* Container Glow */
    .feature-box, .stFileUploader, .record-zone, .stTextArea textarea {
        background: rgba(13, 17, 23, 0.8) !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.1), inset 0 0 10px rgba(56, 189, 248, 0.05) !important;
        color: #e6edf3 !important;
    }

    .feature-box {
        padding: 20px;
        min-height: 400px;
        backdrop-filter: blur(12px);
    }

    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #427083 0%, #588a99 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 4rem !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease !important;
        width: 100%;
    }

    /* Download Button Specific Styling */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #2e7d32 0%, #1b5e20 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        height: 3rem !important;
        width: 100% !important;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(88, 138, 153, 0.5);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 24px; 
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 3px solid #38bdf8 !important;
    }

    /* History Item Styling */
    .history-item {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .history-item:hover {
        background: rgba(56, 189, 248, 0.1);
        border-color: rgba(56, 189, 248, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# --- API HELPER ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(prompt, file_bytes=None, mime=None, text_content=None):
    try:
        parts = []
        if file_bytes:
            parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(file_bytes).decode()}})
        if text_content:
            parts.append({"text": text_content})
        parts.append({"text": prompt})
        # Note: Ensure the model name is correct for your SDK version
        response = client.models.generate_content(model="gemini-2.5-flash", contents=parts)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<h1 class="sidebar-title">📚 LectureLift</h1>', unsafe_allow_html=True)
    st.divider()
    
    db = load_db()
    if db["history"]:
        st.write("### 📼 History")
        # Display clickable buttons for each history item
        for i, item in enumerate(reversed(db["history"][-10:])):
            if st.button(f"📁 {item['name']}", key=f"hist_{i}", use_container_width=True):
                st.session_state.selected_history = item
    
    st.divider()
    if st.button("🗑️ Clear All History", use_container_width=True):
        if DB_PATH.exists():
            os.remove(DB_PATH)
        st.session_state.selected_history = None
        st.rerun()

# --- DISPLAY SELECTED HISTORY (NEW SECTION) ---
if st.session_state.selected_history:
    st.markdown("### 📖 Selected Lecture View")
    with st.container():
        st.markdown(f"**Lecture Name:** {st.session_state.selected_history['name']}")
        st.markdown(f"**Date:** {st.session_state.selected_history['date']}")
        
        # Display the FULL text inside a scrollable box
        st.info(st.session_state.selected_history['text'])
        
        # Add a download button for the specific lecture
        st.download_button(
            label="📥 Download Full Transcription",
            data=st.session_state.selected_history['text'],
            file_name=f"{st.session_state.selected_history['name']}_{st.session_state.selected_history['date']}.txt",
            mime="text/plain"
        )
        
        if st.button("Close Viewer"):
            st.session_state.selected_history = None
            st.rerun()
    st.divider()

# --- MAIN INTERFACE ---
t_upload, t_record = st.tabs(["📄 Document Analysis", "🎙️ Live Lecture"])

with t_upload:
    # Add Clear Selection button at the top
    if st.button("🗑️ Clear Selection", key="clear_upload"):
        st.session_state.upload_data = {"notes": None, "quiz": None, "topics": None}
        st.rerun()
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.write("#### 📤 Input Source")
        input_method = st.radio("Choose Method", ["Upload File", "Paste Text"], horizontal=True, label_visibility="collapsed")
        
        f = None
        pasted_text = None

        if input_method == "Upload File":
            f = st.file_uploader("Upload", type=['pdf','png','jpg','jpeg'], label_visibility="collapsed")
            if f:
                st.success(f"File: {f.name}")
                if not st.session_state.upload_data["topics"]:
                    with st.spinner("Analyzing File..."):
                        st.session_state.upload_data["topics"] = ask_gemini("Extract main topics from this document.", f.getvalue(), f.type)
        else:
            pasted_text = st.text_area("Paste text here", height=300, placeholder="Paste your lecture notes or text content here...", label_visibility="collapsed")
            if pasted_text and not st.session_state.upload_data["topics"]:
                with st.spinner("Analyzing Text..."):
                    st.session_state.upload_data["topics"] = ask_gemini("Extract main topics from this text.", text_content=pasted_text)
    
    with col2:
        st.write("#### 🎯 Key Topics")
        content = st.session_state.upload_data["topics"] or "Waiting for input..."
        st.markdown(f'<div class="feature-box">{content}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom Buttons
    b1, b2 = st.columns(2)
    
    if b1.button("📝 Generate Study Notes", key="up_notes"):
        with st.spinner("Generating Notes..."):
            if input_method == "Upload File" and f:
                st.session_state.upload_data["notes"] = ask_gemini("Create study notes.", f.getvalue(), f.type)
            elif input_method == "Paste Text" and pasted_text:
                st.session_state.upload_data["notes"] = ask_gemini("Create study notes.", text_content=pasted_text)

    if b2.button("📋 Generate Practice Quiz", key="up_quiz"):
        with st.spinner("Creating Quiz..."):
            if input_method == "Upload File" and f:
                st.session_state.upload_data["quiz"] = ask_gemini("Create a quiz.", f.getvalue(), f.type)
            elif input_method == "Paste Text" and pasted_text:
                st.session_state.upload_data["quiz"] = ask_gemini("Create a quiz.", text_content=pasted_text)

    # Display Results
    if st.session_state.upload_data["notes"]: 
        st.info(st.session_state.upload_data["notes"])
        st.download_button("📥 Download Notes", st.session_state.upload_data["notes"], file_name="study_notes.txt")
        
    if st.session_state.upload_data["quiz"]: 
        st.success(st.session_state.upload_data["quiz"])
        st.download_button("📥 Download Quiz", st.session_state.upload_data["quiz"], file_name="practice_quiz.txt")

with t_record:
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.write("#### 🎙️ Live Lecture")
        lec_name = st.text_input("Name", placeholder="Enter lecture name...", label_visibility="collapsed")
        
        st.markdown('<div class="record-zone">', unsafe_allow_html=True)
        audio = audio_recorder(text="Tap to start recording", icon_size="3x", neutral_color="#38bdf8", recording_color="#ef4444")
        st.markdown('</div>', unsafe_allow_html=True)

        if audio:
            if st.button("⚡ Process Audio", use_container_width=True):
                with st.spinner("Transcribing..."):
                    trans = ask_gemini("Transcribe this audio.", audio, "audio/wav")
                    st.session_state.record_data["transcription"] = trans
                    st.session_state.record_data["topics"] = ask_gemini("Extract topics.", text_content=trans)
                    save_to_db({"name": lec_name or "New Lecture", "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "text": trans})
                    st.rerun()

    if st.session_state.record_data["transcription"]:
        st.divider()
        rc1, rc2 = st.columns(2)
        with rc1: 
            st.markdown(f"**Transcription**")
            st.markdown(f"<div class='feature-box'>{st.session_state.record_data['transcription']}</div>", unsafe_allow_html=True)
            st.download_button("📥 Download Transcription", st.session_state.record_data['transcription'], file_name="transcription.txt")
        with rc2: 
            st.markdown(f"**Topics**")
            st.markdown(f"<div class='feature-box'>{st.session_state.record_data['topics']}</div>", unsafe_allow_html=True)