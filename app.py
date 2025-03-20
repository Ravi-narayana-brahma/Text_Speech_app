import streamlit as st
import pandas as pd
import numpy as np
import os
import pydub
import av
import sqlite3
import bcrypt
import base64
import io
import speech_recognition as sr
import smtplib
import re
import time
import random
import hashlib
import easyocr
import pyttsx3
from PIL import Image
from gtts import gTTS
from googletrans import Translator
from pydub import AudioSegment
from tempfile import NamedTemporaryFile
from email.mime.text import MIMEText
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from email.mime.multipart import MIMEMultipart
st.set_page_config(page_title="Word Vibe", page_icon="assests\images\icon.jpg")
CSV_FILE = 'users.csv'
DB_FILE = 'users.db'
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
if "user_details" not in st.session_state:
    st.session_state["user_details"] = None
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            email TEXT,
            phone TEXT,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tts_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            input_text TEXT,
            input_language TEXT,
            output_language TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stt_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            input_language TEXT,
            output_language TEXT,
            transcript TEXT,
            translated_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
def save_tts_history(username, input_text, input_language, output_language):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tts_history (username, input_text, input_language, output_language)
        VALUES (?, ?, ?, ?)
    ''', (username, input_text, input_language, output_language))
    conn.commit()
    conn.close()

def save_stt_history(username, input_language, output_language, transcript, translated_text):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stt_history (username, input_language, output_language, transcript, translated_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, input_language, output_language, transcript, translated_text))
    conn.commit()
    conn.close()
def read_users_from_csv():
    if os.path.exists(CSV_FILE):
        users_df = pd.read_csv(CSV_FILE)
        users_df.columns = users_df.columns.str.strip()
        required_columns = ['username', 'name', 'email', 'phone', 'password']
        for col in required_columns:
            if col not in users_df.columns:
                raise ValueError(f"Missing column in CSV: {col}")
        return users_df
    else:
        # Create the CSV file with the correct headers if it does not exist
        users_df = pd.DataFrame(columns=["username", "name", "email", "phone", "password"])
        users_df.to_csv(CSV_FILE, index=False)
        return users_df
def write_user_to_csv(username, name, email, phone, password):
    new_user = pd.DataFrame([[username, name, email, phone, password]], 
                            columns=["username", "name", "email", "phone", "password"])
    new_user.to_csv(CSV_FILE, mode='a', header=False, index=False)
def write_user_to_db(username, name, email, phone, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, name, email, phone, password) VALUES (?, ?, ?, ?, ?)
    ''', (username, name, email, phone, password))
    conn.commit()
    conn.close()
def register_user(username, name, email, phone, password):
    users_df = read_users_from_csv()
    if username in users_df['username'].values:
        st.error("Username already exists. Please choose a different username.")
        return
    hashed_password = hash_password(password)
    write_user_to_csv(username, name, email, phone, hashed_password)
    write_user_to_db(username, name, email, phone, hashed_password)
def authenticate(username, password):
    users_df = read_users_from_csv()

    # Check in the CSV first
    if username in users_df['username'].values:
        stored_hashed_password = users_df[users_df['username'] == username]['password'].values[0]
        if check_password(stored_hashed_password, password):  # Check if password matches
            # Return user details
            return {
                'username': username,
                'name': users_df[users_df['username'] == username]['name'].values[0],
                'email': users_df[users_df['username'] == username]['email'].values[0],
                'phone': users_df[users_df['username'] == username]['phone'].values[0]
            }
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password, name, email, phone FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result and check_password(result[0], password):  # Check if password matches
        # Return user details
        return {
            'username': username,
            'name': result[1],
            'email': result[2],
            'phone': result[3]
        }

    return None  
def add_bg_image(image_url):
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
                background-image: url({image_url});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                
        }}
            /* Sidebar width customization */
            
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            background: rgba(0,0,0,0); /* Hides header */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
def add_sidebar_image(image_url):
    st.markdown(
        f"""
        <style>
        .stSidebar {{
            background: url({image_url});
            background-size: contain; 
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
def load_image(image_file):
    with open(image_file, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
image_path = "assests/images/app.png"
image_path1 = 'assests/images/user.png'
logo_image = load_image(image_path)
icon_image = load_image(image_path1) 
def add_custom_text_style():
    st.markdown(
        """
        <style>
        h1 { 
            font-family: 'Arial', sans-serif;          
            font-size: 50px;
            color: black;
            letter-spacing: 2px;
            text-align: center;
        }
        button {
            background-color: #33006F;
            color: white;
            font-weight: 900;  /* White text */
            padding: 10px 20px;
            border-radius: 8px;
            border: 2px solid transparent;
            font-size: 20px;
            transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
        }
        p {
            font-weight: 900;
        }
        button:hover {
            background-color: #ffbf00;  /* Darker gold on hover */
            color: #ffffff;  /* White text stays */
            border-color: #ffae42;  /* Orange border on hover */
            box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.5);  /* Gold shadow */
        }
        .stAlert {
            background-color: #ffcccc;
            border-left: 5px solid #ff0000;
            color: #000000;
            font-size: 14px;
            padding: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
def add_custom_text_styles():
    st.markdown(   
        """
        <style>
        .st-emotion-cache-1r4qj8v { /* Example class - check via browser dev tools */
            font-size: 24px;
            color: white;
            font-weight: bold;
        }

        h3 {
            color: #ffff;
            font-weight: bold;
            font-size: 32px;
        }
        .stTextInput input {
            background-color: #f0f0f0;  /* Light gray background */
            border: none;  /* No border */
            border-bottom: 2px solid #4CAF50;  /* Green underline */
            padding: 12px;  /* Padding inside input */
            font-size: 18px;  /* Larger text */
            width: 100%;  /* Full width */
            border-radius: 0;  /* No border-radius, flat design */
            transition: border-bottom-color 0.3s ease-in-out;
        }
        .stTextInput label {
            color: white;
            font-size: 18px ;
        }
        .stTextArea {
            color: white;
               
        }
        /* Focus effect for input fields */
        .stTextInput input:focus {
            border-bottom-color: #2196F3;  /* Blue underline on focus */
            outline: none;  /* No outline */
        }

        /* Placeholder text styling */
        .stTextInput input::placeholder {
            color: #000;  /* Placeholder text color */
            font-style: italic;
            font-weight: bold;
        }
        .stButton button {
            background-color: #33006F;  
            color: white;
            font-weight: 900;  /* White text */
            padding: 10px 20px;
            border-radius: 8px;
            border: 2px solid transparent;
            font-size: 16px;
            transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
        }

        .stButton button:hover {
            background-color: #ffbf00;  /* Darker gold on hover */
            color: #ffffff;  /* White text stays */
            border-color: #ffae42;  /* Orange border on hover */
            box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.5);  /* Gold shadow */
        }
        .stAlert {
            background-color: #ffcccc;
            border-left: 5px solid #ff0000;
            color: #000000;
            font-size: 18px;
            padding: 10px;
        }
        @media (max-width: 640px) {
            /* Modify heading style for smaller screens */
            h1 {
                font-size: 35px;
                padding-left: 240px;
            }
        @media (min-width: 641px and max-width: 1200px) {
            h1 {
                padding-left: 10px;
            }
        }   
        }
        </style>
        """,
        unsafe_allow_html=True
    )
def add_responsive_css():
    """Injects responsive CSS to fix small screen layout issues."""
    st.markdown("""
        <style>
        /* Small Screens: Mobile Phones (Max 640px) */
        @media (max-width: 640px) {
            /* Stack columns vertically */
            .st-emotion-cache-1r4qj8v {
                flex-direction: column !important;
            }

            /* Adjust heading sizes inside columns */
            .stColumns h1 {
                font-size: 28px !important;
                text-align: center !important;
                width: 100% !important;
                display: block;
            }
            /* Adjust main heading size */
            h1 {
                font-size: 36px !important;
                text-align: center !important;
                margin-left: 37px !important;
                margin-top: -34px !important;
            }

            /* Adjust buttons inside .stButton */
            .stButton > button {
                font-size: 16px !important;
                padding: 10px !important;
                width: 100% !important;
            }

            /* Modify text input fields */
            .stTextInput input, .stTextArea textarea {
                font-size: 16px !important;
                padding: 8px !important;
                width: 100% !important;
            }

            /* Ensure images are responsive */
            .stImage {
                width: 50% !important;
                display: block;
                margin: 0 auto;
            }
        }
        </style>
    """, unsafe_allow_html=True)
def handle_password_recovery(input_value):
    # Simple check to differentiate between email and phone numbe
    message = f"Password recovery instructions sent to <strong>{input_value}</strong> via SMS."

    # Create a styled success message
    success_message = f"""
    <div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb;">
        {message}
    </div>
    """
    st.markdown(success_message, unsafe_allow_html=True)
# Home Page Content
def show_home_page():
    # Display the selected card functionality if a card is selected
    if st.session_state.selected_card == "Text to Speech":
        show_text_to_speech()
    elif st.session_state.selected_card == "Speech to Text":
        show_speech_to_text()
    elif st.session_state.selected_card == "Text to Text":
        show_text_to_text_translation()
    elif st.session_state.selected_card == "Image to Speech":
        show_image_to_text_to_speech()
    else:
        # Show home page cards only if no card is selected
        st.markdown(
            """
            <style>
                [data-testid="stAppViewContainer"] {
                    background: linear-gradient(135deg, #9b59b6, #1abc9c);
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }
                /* Custom CSS for big square buttons */
                .stButton > button {
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-end;
                    align-items: center;
                    width: 100%;
                    height: 150px; /* Adjust height as needed */
                    background: linear-gradient(135deg, #33006F, #6A0DAD); /* Gradient background */
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 15px;
                    border: none;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.3s;
                    margin: 10px 0;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2); /* Subtle shadow */
                    position: relative;
                    overflow: hidden;
                    transform-style: preserve-3d;
                }

                .stButton > button::before {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 300%;
                    height: 300%;
                    background: radial-gradient(circle, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 70%);
                    transform: translate(-50%, -50%) scale(0);
                    transition: transform 0.5s ease-out;
                    pointer-events: none;
                }

                .stButton > button:hover {
                    background: linear-gradient(135deg, #4B0082, #8A2BE2); /* Brighter gradient on hover */
                    transform: scale(1.05) translateZ(20px);
                    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); /* Enhanced shadow on hover */
                }

                .stButton > button:active {
                    transform: scale(0.95) translateZ(20px);
                }

                .stButton > button:hover::before {
                    transform: translate(-50%, -50%) scale(1);
                }

                .stButton > button i {
                    font-size: 32px;
                    margin-bottom: 10px;
                }
                [data-testid="stHeader"], [data-testid="stToolbar"] {
                    background: rgba(0,0,0,0); /* Hides header */
                }
                @media (max-width: 640px) {
                    h1 {
                        font-size: 29px !important;
                        text-align: center !important;
                        margin-left: 100px !important;
                        margin-top: -90px !important;
                    }
                    .stImage {
                        width: 63% !important;
                        display: block;
                        margin: 0 auto;
                    }
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            st.image(image_path, width=130)
        with col2:
            st.markdown('<h1 style=" color: white; text-align: center; margin-left: -238px; margin-top: 20px; font-family: Arial, sans-serif;">Welcome to WordVibe!</h1>', unsafe_allow_html=True)
        
        # Check if user details are available in session state
        if "user_details" in st.session_state and st.session_state["user_details"] is not None:
            user_details = st.session_state["user_details"]
            greeting_message = f"Hello, {user_details['username']}!"
        else:
            greeting_message = "Hello, Guest!"
        st.markdown(f"""
            <h3 style="text-align: left; color: white; font-family: Arial, sans-serif;">
                {greeting_message}
            </h3>
        """, unsafe_allow_html=True)
        
        # Create big square buttons using st.button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Text to Speech", key="text_to_speech"):
                st.session_state.selected_card = "Text to Speech"
                st.rerun()
        with col2:
            if st.button("🎤 Speech to Text", key="speech_to_text"):
                st.session_state.selected_card = "Speech to Text"
                st.rerun()

        col3, col4 = st.columns(2)
        with col3:
            if st.button("📝 Text to Text", key="text_to_text"):
                st.session_state.selected_card = "Text to Text"
                st.rerun()
        with col4:
            if st.button("📷 Image to Speech", key="image_to_speech"):
                st.session_state.selected_card = "Image to Speech"
                st.rerun()
def show_login_page():
    add_bg_image("https://azure.microsoft.com/es-es/blog/wp-content/uploads/sites/4/2024/02/Azure_Blog_Abstract-07_1260x708-1-1024x575.jpg")
    add_custom_text_styles()
    add_responsive_css()
    col1, col2 = st.columns(2)
    with col1:
        params = st.query_params
        screen_width = int(params.get("width", [1200])[0])  # Default to 800px if width is not found

        new_width = int(screen_width * 0.15)  # Adjust image width to 30% of screen width
        st.image(image_path, width=new_width)
    with col2:
        st.markdown('<h1 style=" color: black; text-align: center; margin-left: -238px; margin-top: 40px; font-family: Arial, sans-serif; ">Welcome to WordVibe!</h1>', unsafe_allow_html=True)
    st.markdown("<h3 style='color: black; font-weight: bold;'>Sign In</h3>",unsafe_allow_html=True)
    username = st.text_input("Username", key="login_username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
    # Login button
    if st.button("Login"):
        if username == "" or password == "":
            st.error("Please enter both username and password.")
        else:
            # Call the authenticate function to check credentials
            user_details = authenticate(username, password)
            if user_details:  # Check if authentication was successful
                # Update session state
                st.session_state["user_details"] = user_details
                st.session_state["show_login"] = False
                st.session_state["show_home_page"] = True
                st.rerun()  # Rerun the app to reflect the changes
            else:
                st.error("Invalid Username or Password.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("New User? Sign Up"):
            st.session_state["show_signup"] = True
            st.session_state["show_login"] = False
            st.rerun()

    with col2:
        if st.button("Forgot Password?"):
            st.session_state["show_recovery"] = True
            st.session_state["show_login"] = False
            st.rerun()

    # Continue Without Login button
    if st.button("Continue Without Login"):
        st.session_state["show_home_without_login"] = True
        st.session_state["show_login"] = False
        st.rerun()
def show_signup_page():
    add_bg_image("https://azure.microsoft.com/es-es/blog/wp-content/uploads/sites/4/2024/02/Azure_Blog_Abstract-07_1260x708-1-1024x575.jpg")
    add_custom_text_styles()
    st.markdown("<h3 style='color: white; font-weight: bold;'>Sign Up</h3>",unsafe_allow_html=True)
    # Input fields
    username_signup = st.text_input("Username", placeholder="Enter a username")
    name_signup = st.text_input("Name", placeholder="Your full name")
    email_signup = st.text_input("Email", placeholder="Enter a Email Address")
    phone_signup = st.text_input("Phone", placeholder="Enter a phone number")
    password_signup = st.text_input("Password", placeholder="Choose a password", type="password")

    # Sign Up button
    if st.button("Sign Up", key="signup_button"):
        if username_signup and name_signup and email_signup and phone_signup and password_signup:
            register_user(username_signup, name_signup, email_signup, phone_signup, password_signup)
            st.success("User Sign in successfully! Please Login")
            st.rerun()
        else:
            st.error("Please fill in all fields.")
    # Back to Login button
    if st.button("Back to Login"):
        st.session_state["show_login"] = True
        st.session_state["show_signup"] = False
        st.rerun()
def show_password_recovery_page():
    add_bg_image("https://azure.microsoft.com/es-es/blog/wp-content/uploads/sites/4/2024/02/Azure_Blog_Abstract-07_1260x708-1-1024x575.jpg")
    add_custom_text_styles()
    st.markdown("<h3 style='color: white; font-weight: bold;'>Password Recovery</h3>",unsafe_allow_html=True)
    recovery_input = st.text_input("Enter your  phone number for password recovery", placeholder="Your phone number")
    # Recover Password Button
    if st.button("Recover Password"):
        if recovery_input:
            # Check if the input is a valid 10-digit phone number
            if recovery_input.isdigit() and len(recovery_input) == 10:
                handle_password_recovery(recovery_input)  # Pass the single input
            else:
                st.error("Please enter a valid 10-digit phone number.")
        else:
            st.error("Please enter your phone number for recovery.")

    # Back to Login Button
    if st.button("Back to Login"):
        st.session_state["show_login"] = True
        st.session_state["show_recovery"] = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
def show_without_login_home_page():

    st.title("Home Page (No Login Required)")
    st.write("You are viewing the app with limited access. Log in for full access.")

SUPPORTED_LANGUAGES = {
    "Afrikaans": "af",
    "Albanian": "sq",
    "Amharic": "am",
    "Arabic": "ar",
    "Assamese": "as",
    "Bengali": "bn",
    "Bosnian": "bs",
    "Bulgarian": "bg",
    "Catalan": "ca",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Filipino (Tagalog)": "fil",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Kannada": "kn",
    "Korean": "ko",
    "Malay": "ms",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Nepali": "ne",
    "Norwegian": "no",
    "Odia (Oriya)": "or",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Spanish": "es",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tamil": "ta",
    "Telugu": "te",
    "Turkish": "tr",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Yoruba": "yo",
    "Zulu": "zu"
}

translator = Translator()
r = sr.Recognizer()
# Function to convert text to speech
def text_to_speech(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        output_file = "output.mp3"
        tts.save(output_file)
        return output_file
    except Exception as e:
        print(f"Error in text-to-speech conversion: {e}")
        return None
# Function to get available voices
def get_available_voices():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    return voices    
# Function to translate text
def translate_text(text, source_language, dest_language):
    translator = Translator()
    try:
        translated = translator.translate(text, src=source_language, dest=dest_language)
        return translated.text
    except Exception as e:
        st.error(f"Error in translation: {e}")
        return None
# Function to recognize speech from audio file
def speech_to_text(audio_file, language_code):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language_code)
            return text
            
    except sr.UnknownValueError:
        
        st.markdown(
                """
                <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                            padding: 10px; border-radius: 8px; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                    Could not understand the audio
                </div>
                """,
                unsafe_allow_html=True
        )
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Web Speech API; {e}")
        return None
# Function to recognize speech from microphone
def recognize_from_microphone(language_code):
    recognizer = sr.Recognizer()

    # Adjust settings for better recognition
    recognizer.pause_threshold = 1.0  
    recognizer.energy_threshold = 400  

    # 🔍 Check if a microphone exists before using it
    try:
        if pyaudio.PyAudio().get_default_input_device_info():  
            with sr.Microphone() as source:
                st.markdown(
                    """
                        <div style="font-size: 18px; color: #fff; background-color: rgb(30, 9, 150); 
                                padding: 20px; border-radius: 8px; 
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Adjusting for ambient noise... Please wait.
                        </div>
                    """,
                    unsafe_allow_html=True
                )
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                st.markdown(
                    """
                        <div style="font-size: 18px; color: #fff; background-color: rgb(30, 9, 150); 
                                padding: 20px; border-radius: 8px; margin-top: 15px;
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Listening... Please speak into the microphone.
                        </div>
                    """,
                    unsafe_allow_html=True
                )

                audio_data = recognizer.listen(source)
                
                st.markdown(
                    """
                        <div style="font-size: 18px; color: #fff; background-color: rgb(30, 9, 150); 
                                padding: 20px; border-radius: 8px; margin-top: 15px;
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Processing audio...
                        </div>
                    """,
                    unsafe_allow_html=True
                )

                text = recognizer.recognize_google(audio_data, language=language_code)
                return text
        else:
            raise OSError("No microphone found")
    
    except OSError:
        st.error("No microphone detected. Please upload an audio file instead.")
        return ""

    except sr.UnknownValueError:
        st.markdown(
            """
            <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                        padding: 20px; border-radius: 8px; margin-top: 15px; 
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                Could not understand the audio. Please try again.
            </div>
            """,
            unsafe_allow_html=True
        )
    
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Web Speech API; {e}")
def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        audio_format = uploaded_file.name.split('.')[-1].lower()
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_path = temp_audio_file.name
            audio = AudioSegment.from_file(uploaded_file, format=audio_format)
            audio.export(audio_path, format="wav")
        return audio_path
    return None
def show_text_to_speech():
    add_bg_image("https://static.vecteezy.com/system/resources/previews/024/461/751/non_2x/abstract-gradient-green-blue-liquid-wave-background-free-vector.jpg")
    st.markdown("""
        <style>
        /* Small Screens: Mobile Phones (Max 640px) */
        @media (max-width: 640px) {
            h1 {
                font-size: 23px !important;
                text-align: center !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    # Ensure the user is logged in
    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
        languages = SUPPORTED_LANGUAGES
    else:
        languages = LIMITED_LANGUAGES

    st.markdown(
        """
        <style>
            .stTextArea {
                background-color: #f0f0f0;
                border: 3px solid #0000;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
                color: #333;
                width: 100%;
                min-height: 100px;
            }
            .stTextArea:focus {
                border-color: #0056b3;
                box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
            }
            .stSelectbox {
                background-color: #f0f0f0;
                border: 2px solid #007bff;
                border-radius: 10px;
                padding: 10px;
                color: #333;
            }
            .stSelectbox select {
                background-color: #fff;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-size: 16px;
                color: #333;
            }
            .stSelectbox select:focus {
                outline: none;
                box-shadow: 0 0 5px rgba(0, 123, 255, 0.5);
            }

            /* History section styles */
            .history-header {
                color: white; /* Gold color for header */
                font-size: 36px;
                font-weight: bold;
                text-align: center;
                margin-top: 50px;
                font-family: 'Arial', sans-serif;
                text-transform: uppercase;
                letter-spacing: 2px;
            }

            /* Styling for the dataframe */
            .stDataFrame {
                background-color: transparent;
            }
            
            .stDataFrame thead th {
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }

            .stDataFrame tbody tr:hover {
                background-color: #f1f1f1; /* Light grey background on row hover */
                cursor: pointer;
            }

            /* Padding between sections */
            .section-spacing {
                margin-bottom: 50px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown('<h1 style="font-size: 40px; font-weight: 900; color: white; text-align: center; font-family: Arial, sans-serif;">🔊 Multilingual Text to Speech with Translation</h1>', unsafe_allow_html=True)

    # Input fields
    text_input = st.text_area("Enter the text you want to convert to speech:")
    input_language = st.selectbox("Select the input language for text recognition:", list(languages.keys()))
    output_language = st.selectbox("Select the output language for translation:", list(languages.keys()))

    # Convert to Speech button
    if st.button("Convert to Speech"):
        if text_input:
            input_lang_code = SUPPORTED_LANGUAGES[input_language]
            output_lang_code = SUPPORTED_LANGUAGES[output_language]

            translated_text = translate_text(text_input, input_lang_code, output_lang_code)

            if translated_text:
                output_file = text_to_speech(translated_text, output_lang_code)

                if output_file:
                    with open(output_file, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.markdown(
                        f"""
                        <div style="font-size: 18px; color: #fff; background-color: rgba(7, 228, 36, 0.88); 
                                    padding: 10px; border-radius: 8px; 
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Text translated and converted to speech in '{output_language}'
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    # Save TTS history if logged in
                    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
                        username = st.session_state["user_details"]["username"]
                        save_tts_history(username, text_input, input_language, output_language)
                else:
                    st.markdown(
                        """
                        <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                                    padding: 10px; border-radius: 8px; text-align: center; 
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Failed to generate audio file.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    """
                    <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                                padding: 10px; border-radius: 8px; text-align: center; 
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                        Translation failed. Please check the input language.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                """
                <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                            padding: 10px; border-radius: 8px; text-align: center; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                    Please enter some text to translate.
                </div>
                """,
                unsafe_allow_html=True
            )
    # Display TTS history if logged in
    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
        st.markdown('<h3 style="font-size: 30px; color: white; text-align: center;">TTS History</h3>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        tts_history_df = pd.read_sql_query(f'''
            SELECT input_text, input_language, output_language, timestamp 
            FROM tts_history 
            WHERE username = "{st.session_state["user_details"]["username"]}"
            ORDER BY timestamp DESC
        ''', conn)
        conn.close()
        st.dataframe(tts_history_df)
    else:
         st.markdown(
                """
                <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                            padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                    You must be logged in to Save & view TTS history.
                </div>
                """,
                unsafe_allow_html=True
            )
def translate_text(text, source_language, target_language):
    """
    Translates text from the source language to the target language.
    """
    result = translator.translate(text, src=source_language, dest=target_language)
    return result.text
def split_audio(audio_segment, chunk_length):
    """
    Splits an audio segment into smaller chunks of given length (in milliseconds).
    """
    chunks = pydub.utils.make_chunks(audio_segment, chunk_length)
    return chunks
# Function to transcribe audio, skipping unrecognized chunks
def transcribe_audio(audio_file, language):
    """
    Transcribes an audio file using Google Speech Recognition, skipping unrecognized chunks.
    """
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
        try:
            # Attempt to recognize the audio
            return r.recognize_google(audio, language=language)
        except sr.UnknownValueError:
            # Skip and return an empty string if audio is unrecognized
            return ""
        except sr.RequestError as e:
            return "Could not request results from Google Speech Recognition service; {0}".format(e)
# Function to process each audio chunk and skip unrecognized chunks
def process_audio_chunks(chunks, language):
    """
    Processes each audio chunk and transcribes only recognized chunks.
    """
    transcript = []
    for i, chunk in enumerate(chunks):
        chunk.export(f"chunk{i}.wav", format="wav")
        recognized_text = transcribe_audio(f"chunk{i}.wav", language)
        if recognized_text:  # Only append non-empty recognized text
            transcript.append(recognized_text)
    return " ".join(transcript)
output_folder = "output_audio/"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
# Save the uploaded audio to the specified folder
# Initialize SQLite connection (or create database if not exists)
LIMITED_LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "Hindi": "hi",
    "Bengali": "bn",
    "German": "de"
}
def show_text_to_text_translation():
    # Modern Minimalist CSS with Gradient Background
    add_bg_image("https://static.vecteezy.com/system/resources/previews/024/461/751/non_2x/abstract-gradient-green-blue-liquid-wave-background-free-vector.jpg")
    
    # Custom CSS for a modern and attractive design
    st.markdown(
        """
        <style>
            /* Page Background */
            body {
                background: linear-gradient(to right, #283c86, #45a247);
                color: white;
                font-family: 'Arial', sans-serif;
            }
            /* Input Fields */
            .stTextInput, .stSelectbox {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid #00c896;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                color: white !important;
                margin-bottom: 15px;
            }

            /* Translated Text Box */
            .translated-box {
                background: rgba(255, 255, 255, 0.9);
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #00c896;
                font-size: 20px;
                color: black;
                text-align: center;
                font-weight: bold;
                margin-top: 20px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            }

            /* Button Styling */
            .stButton button {
                background-color: #00c896;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s, transform 0.2s;
            }

            .stButton button:hover {
                background-color: #009e7a;
                transform: scale(1.05);
            }

            /* Title Styling */
            .title {
                font-size: 40px;
                font-weight: bold;
                color: #fffff;
                text-align: center;
                margin-bottom: 20px;
            }

            /* Subtitle Styling */
            .subtitle {
                font-size: 20px;
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Page Title
    st.markdown(
        '<h1 class="title" style="color: white; font-size: 40px; text-align: center; font-weight: bold;">🌍 Simple Text Translator</h1>', 
        unsafe_allow_html=True
    )
    # Centered Container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    # Input Fields
    input_lang = st.selectbox("From Language", list(SUPPORTED_LANGUAGES.keys()))
    output_lang = st.selectbox("To Language", list(SUPPORTED_LANGUAGES.keys()))
    input_text = st.text_input("Type text to translate:", placeholder="Enter your text here...")

    # Translate Button
    if st.button("Translate", key="translate_button"):
        if input_text:
            translated_text = translate_text(input_text, SUPPORTED_LANGUAGES[input_lang], SUPPORTED_LANGUAGES[output_lang])
            st.markdown(
                f"""
                <div class="translated-box">
                    <strong>📝 Translated Text:</strong><br><br>
                    {translated_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                            padding: 10px; border-radius: 8px; text-align: center; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                    Please enter some text to translate.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)
import tempfile

# ✅ Initialize EasyOCR Reader
reader = easyocr.Reader(["en"], download_enabled=True, model_storage_directory="models/")

def text_to_speech(text, lang="en"):
    tts = gTTS(text=text, lang=lang)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def show_image_to_text_to_speech():
    add_bg_image("https://static.vecteezy.com/system/resources/previews/024/461/751/non_2x/abstract-gradient-green-blue-liquid-wave-background-free-vector.jpg")
    st.markdown('<h1 style="font-size: 40px; color: white; text-align: center;">🖼️ Image to Text-to-Speech</h1>', unsafe_allow_html=True)
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        try:
            image = Image.open(uploaded_image).convert("RGB")  # Ensure RGB mode
            # Resize the image to a maximum width of 800 pixels
            max_width = 800
            width_percent = (max_width / float(image.size[0]))
            height_size = int((float(image.size[1]) * float(width_percent)))
            image = image.resize((max_width, height_size), Image.Resampling.LANCZOS)
            
            st.image(image, use_container_width=True)
    
            # Convert Image to NumPy Array for EasyOCR
            img_np = np.array(image)
    
            # Use EasyOCR to Extract Text
            extracted_text = reader.readtext(img_np, detail=0)  # Returns a list of words
            extracted_text = " ".join(extracted_text)  # Convert list to string
    
            # Display Extracted Text
            st.markdown(f"""
                <div style="background-color: #262626; color: #ffffff; padding: 20px; border-radius: 12px; font-size: 20px;">
                    <strong style="font-size: 22px; text-decoration: underline;">Extracted Text:</strong>
                    <p style="margin-top: 10px;">{extracted_text}</p>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("🔊 Convert to Speech", key="tts_button"):
                output_file = text_to_speech(extracted_text, "en")
                if output_file:
                    st.audio(output_file, format="audio/mp3")
        except Exception as e:
            st.error(f"Error processing image: {e}")
def show_speech_to_text():
    add_bg_image("https://static.vecteezy.com/system/resources/previews/023/669/544/non_2x/abstract-gradient-green-blue-liquid-wave-background-free-vector.jpg")
    # Check if the user is logged in
    st.markdown("""
        <style>
        /* Small Screens: Mobile Phones (Max 640px) */
        @media (max-width: 640px) {
            h1 {
                font-size: 23px !important;
                text-align: center !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
        languages = list(SUPPORTED_LANGUAGES.items())
    else:
        languages = list(LIMITED_LANGUAGES.items())

    st.markdown('<h1 style="font-size: 50px; font-weight: 900; color: orange; text-align: center; font-family: Arial, sans-serif;">🎤 Multilingual Speech to Text with Translation</h1>', unsafe_allow_html=True)
    st.markdown("""
        <style>
            h3 {
                color: white;     
            }
            
            .stSelectbox {
                background-color: #f0f0f0; /* Background color for selectbox */
                border: 2px solid #007bff; /* Border color for selectbox */
                border-radius: 10px; /* Rounded corners */
                padding: 10px; /* Padding inside the selectbox */
                color: #333; /* Text color inside the selectbox */
            }
            .stSelectbox select {
                background-color: #fff; /* Background color for the dropdown */
                border: none; /* No border for the dropdown */
                border-radius: 5px; /* Rounded corners for dropdown */
                padding: 5px; /* Padding inside the dropdown */
                font-size: 16px; /* Font size */
                color: #333; /* Text color inside the dropdown */
            }
            .stSelectbox select:focus {
                outline: none; /* Remove outline when focused */
                box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); /* Shadow effect when focused */
            }
            .stFileUploader {
                background-color: #f0f0f0; /* Background color */
                    border: 2px dashed #007bff; /* Border color */
                    border-radius: 10px; /* Rounded corners */
                    padding: 20px; /* Padding inside the box */
                    text-align: center; /* Center the text */
                    color: #007bff; /* Text color */
                    font-size: 18px; /* Font size */
            }
            .stFileUploader:hover {
                background-color: #e0e0e0; /* Background color on hover */
                border-color: #0056b3; /* Border color on hover */
            }
        </style>
    """, unsafe_allow_html=True)
    # Input fields
    input_language = st.selectbox("Select the input language for speech recognition:", languages, key="input_language")
    output_language = st.selectbox("Select the output language for translation:", languages, key="output_language")

    # Input method selection
    input_choice = st.selectbox("Choose input method:", ["Record live voice", "Upload audio file"])

    # Initialize transcript and translated_text
    transcript = ""
    translated_text = ""

    # Handling audio file upload
    if input_choice == "Upload audio file":
        with st.form("upload_audio"):
            st.subheader("Upload an audio file")
            audio_file = st.file_uploader("Upload Audio", type=["mp3", "wav"])
            if st.form_submit_button("Upload"):
                if audio_file:
                    st.markdown(
                        """
                            <div style="font-size: 18px; color: #fff; background-color: rgb(30, 9, 150); 
                                    padding: 20px; border-radius: 8px; margin-top: 15px;
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                                Wait, processing audio...
                            </div>
                        """,
                        unsafe_allow_html=True
                    )
                    audio_segment = AudioSegment.from_file(audio_file)
                    output_folder = "output_audio/"
                    os.makedirs(output_folder, exist_ok=True)
                    audio_segment.export(os.path.join(output_folder, "uploaded_audio.wav"), format="wav")
                    chunks = split_audio(audio_segment, 1000)

                    transcript = ""
                    for i, chunk in enumerate(chunks):
                        chunk_file_path = os.path.join(output_folder, f"chunk_{i}.wav")
                        chunk.export(chunk_file_path, format="wav")
                        recognized_text = transcribe_audio(chunk_file_path, input_language[1])
                        if recognized_text:  # Only append non-empty recognized text
                            transcript += recognized_text + " "  # Add a space between chunks

                    if transcript:  # Check if transcript is not empty
                        translated_text = translate_text(transcript, input_language[1], output_language[1])
                        st.markdown(
                            """
                            <div style="font-size: 23px; color: #fff; background-color: rgba(7, 228, 36, 0.88); 
                                    padding: 20px; border-radius: 8px;
                                    margin-top: 20px; 
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                                    Audio Processed Successfully!
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.text_area("Transcript", value=transcript, height=200)  # Display transcript in a text area
                        st.markdown(f'''<p class="translated">🌍 **Translated Text:** {translated_text}</p>''', unsafe_allow_html=True)

                        # Save STT history if transcript and translated_text are available
                        if transcript and translated_text:
                            if "user_details" in st.session_state and st.session_state["user_details"] is not None:
                                username = st.session_state["user_details"]["username"]
                                save_stt_history(username, input_language[1], output_language[1], transcript, translated_text)
                            else:
                                st.markdown(
                                    """
                                    <div style="font-size: 23px; color: #fff; background-color: rgba(247, 14, 14, 0.88); 
                                            padding: 20px; border-radius: 8px;
                                            margin-top: 30px; 
                                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                                            You must be logged in to save history.
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                    else:
                        st.markdown(
                            """
                            <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                                    padding: 10px; border-radius: 8px; text-align: center; 
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                                No transcript available. Please try again.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                else:
                    st.markdown(
                        """
                        <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                                padding: 10px; border-radius: 8px; text-align: center; 
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Please upload an audio file.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # Handling live voice recording
    elif input_choice == "Record live voice":
        if st.button("Start Recording"):
            recognized_text = recognize_from_microphone(input_language[1])
            if recognized_text:
                translated_text = translate_text(recognized_text, input_language[1], output_language[1])

                st.markdown(
                    f"""
                    <div style="font-size: 23px; color: #fff; background-color: rgba(7, 228, 36, 0.88); 
                            padding: 20px; border-radius: 8px; margin-top: 20px; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Recognized Text: {recognized_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"""
                    <div style="font-size: 23px; color: #fff; background-color: rgba(7, 228, 36, 0.88); 
                            padding: 20px; border-radius: 8px;
                            margin-top: 20px; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                            Translated Text: {translated_text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Save STT history if recognized text and translated text are available
                if recognized_text and translated_text:
                    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
                        username = st.session_state["user_details"]["username"]
                        save_stt_history(username, input_language[1], output_language[1], recognized_text, translated_text)
                    else:
                        st.markdown(
                            """
                            <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                                    padding: 10px; border-radius: 8px; text-align: center;
                                    margin-top: 20px; 
                                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                                You must be logged in to view TTS history.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
            else:
                st.markdown(
                    """
                    <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                            padding: 20px; border-radius: 8px; margin-top: 15px; 
                            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                        Speech recognition failed. Please try again.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Display STT history if logged in
    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
        st.markdown('<h3 style="font-size: 30px; color: white; text-align: center;">STT History</h3>', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        stt_history_df = pd.read_sql_query(f'''
            SELECT input_language, output_language, transcript, translated_text, timestamp 
            FROM stt_history 
            WHERE username = "{st.session_state["user_details"]["username"]}"
            ORDER BY timestamp DESC
        ''', conn)
        conn.close()

        # Display the DataFrame in the app
        st.dataframe(stt_history_df)
friendly_faq_knowledge_base = {
    "Hello! How are you?": [
        "I'm just a computer program, but I'm here to help you! How can I assist you today?"
    ],
    "What is your name?": [
        "I'm your friendly Text-to-Speech assistant! You can call me TTS Buddy."
    ],
    "What can you do?": [
        "I can help you convert text to speech, transcribe audio files, and answer your questions about the application!"
    ],
    "What time is it?": [
        "I don't have a watch, but you can check your device's clock for the current time!"
    ],
    "Can you help me with my questions?": [
        "Absolutely! Feel free to ask me anything related to the Text-to-Speech application."
    ],
    "What is Text-to-Speech (TTS)?": [
        "Text-to-Speech is a technology that converts written text into spoken words. I can help you convert your text into audio!"
    ],
    "What is Speech-to-Text (STT)?": [
        "Speech-to-Text is a technology that converts spoken language into written text. I can transcribe your audio files into text!"
    ],
    "How do I upload an audio file?": [
        "You can use the upload button in the application to select and upload your audio file for transcription."
    ],
    "What audio formats can I upload?": [
        "You can upload audio files in MP3 or WAV formats for transcription."
    ],
    "How accurate is the transcription?": [
        "The accuracy of the transcription depends on the audio quality and clarity of speech. Generally, it performs well with clear audio."
    ],
    "Can I customize the voice in TTS?": [
        "Yes! You can choose different voices and adjust the speed and pitch to suit your preferences."
    ],
    "How do I save the audio output?": [
        "Once the text is converted to speech, you can download the audio file directly from the application."
    ],
    "Can I use different languages for TTS and STT?": [
        "Yes! The application supports multiple languages for both Text-to-Speech and Speech-to-Text functionalities."
    ],
    "Do I need to create an account to use this application?": [
        "Creating an account is optional, but it allows you to save your preferences and access your history."
    ],
    "How do I create an account?": [
        "You can create an account by clicking on the 'Sign Up' button and filling out the required information."
    ],
    "How do I log in?": [
        "You can log in using your registered email and password on the login page."
    ],
    "What should I do if I forget my password?": [
        "You can click on the 'Forgot Password' link on the login page to reset your password."
    ],
    "How do I update my account information?": [
        "You can update your account information in the 'Account' section after logging in."
    ],
    "How do I delete my account?": [
        "You can request account deletion in the account settings or contact support for assistance."
    ],
    "What are your favorite things to do?": [
        "I love helping users like you! Whether it's converting text to speech or answering questions, that's what I do best!"
    ],
    "Do you have feelings?": [
        "I don't have feelings like humans do, but I'm programmed to be friendly and helpful!"
    ],
    "Can you tell me a joke?": [
        "Sure! Why did the computer go to the doctor? Because it had a virus!"
    ],
    "Can I talk to you anytime?": [
        "Yes! I'm here 24/7, ready to assist you whenever you need help."
    ],
    "Are you a real person?": [
        "No, I'm not a real person. I'm an AI chatbot created to assist you with the Text-to-Speech application."
    ],
    "Do you have any hobbies?": [
        "I don't have hobbies, but I enjoy helping you with your questions and tasks!"
    ],
    "What's the best way to learn more about this application?": [
        "The best way to learn is to explore the features and try them out. You can also check the help section for more information!"
    ],
    "How do I provide feedback?": [
        "You can provide feedback through the feedback form located in the settings or help section of the application."
    ],
    "Can I make suggestions for new features?": [
        "Of course! Your suggestions are always welcome, and they can help improve the application."
    ],
    "What's your favorite type of text to convert to speech?": [
        "I enjoy converting all types of text! Whether it's stories, articles, or any written content, I'm here for it!"
    ],
    "How long have you been around?": [
        "I've been here since the launch of this Text-to-Speech application, ready to help users like you!"
    ],
    "Do you have a favorite language?": [
        "I don't have preferences, but I can work with many languages! What language would you like to use today?"
    ],
    "What's your favorite color?": [
        "I don't see colors like humans do, but blue is often considered calming and friendly!"
    ],
    "Can you speak in different accents?": [
        "Yes! I can emulate various accents based on the text-to-speech settings. Which accent would you like to hear?"
    ],
    "What's the meaning of life?": [
        "That's a deep question! Many say it's about finding happiness, helping others, and pursuing your passions."
    ],
}
def chatbot_response(user_input):
    """Generate a response from the chatbot based on user input."""
    user_name = st.session_state.get("user_details", {}).get("username", "User")
    # Define responses based on user input
    greetings = ["hello", "hi"]
    farewell = ["bye", "goodbye", "see you"]
    user_input = user_input.lower()  # Normalize the input
    # Check for greetings
    for greeting in greetings:
        if greeting in user_input:
            return f"Hello, {user_name}! How can I assist you today?"
    # Check for farewells
    for farewell_word in farewell:
        if farewell_word in user_input:
            return "Goodbye! Have a great day!"
    # Check for FAQs
    for question in friendly_faq_knowledge_base.keys():
        if question.lower() in user_input:
            return friendly_faq_knowledge_base[question]  # Return the response(s)
    # If no matches found
    return "I'm sorry, I didn't understand that. Please ask about features like Text to Speech or Speech to Text."
def show_help_page():
    add_bg_image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMbPuKBpyPFBWdo9-8bse0SM3GzlkWasC-Vw&usqp=CAU")

    # Check if the user is logged in
    if "user_details" not in st.session_state or st.session_state["user_details"] is None:
        st.markdown(
            """
            <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                        padding: 10px; border-radius: 8px; text-align: center; 
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                You must log in to access the Help & Support page.
            </div>
            """,
            unsafe_allow_html=True
        )
        return  # Exit the function if the user is not logged in

    # If the user is logged in, display the Help & Support page
    st.markdown(
        """
        <h1 style="font-size: 50px; color: black; text-align: center; 
                    margin-bottom: 20px; font-weight: bold;">
            Help & Support
        </h1>
        """,
        unsafe_allow_html=True
    )

    # Display the message with inline CSS
    st.markdown(
        """
        <div style="font-size: 22px; color: black; text-align: left; 
                    margin-bottom: 30px; padding: 10px; font-weight: 900;">
            Ask me anything about the app!
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # User input
    st.markdown('<h6 style=" color: black; font-weight: 600; font-family: Arial, sans-serif;">You:</h6>', unsafe_allow_html=True)
    user_input = st.text_input(
        "", 
        key="user_input", 
        help="Type your message here.", 
        placeholder="Type your message...", 
        label_visibility="visible", 
        max_chars=500, 
        disabled=False
    )

    # Apply custom CSS class to the input
    st.markdown("<style>.stTextInput > div > input { class: custom-input; }</style>", unsafe_allow_html=True)

    # Handle the "Send" button click
    if st.button("Send"):
        if user_input:
            # Store user input in chat history
            st.session_state.chat_history.append({"sender": "User", "message": user_input})
            # Get bot response
            response = chatbot_response(user_input)
            # Store bot response in chat history
            st.session_state.chat_history.append({"sender": "Bot", "message": response})
            # Clear input field (not necessary since Streamlit handles this)
            user_input = ""  
        else:
            st.warning("Please enter your doubt.")

    # Display chat history in a structured format
    st.markdown('<h3 style=" color: black; font-family: Arial, sans-serif;">Chat History</h3>', unsafe_allow_html=True)
    for index, chat in enumerate(st.session_state.chat_history):
        if isinstance(chat, dict) and "sender" in chat and "message" in chat:
            if chat["sender"] == "User":
                st.markdown(
                    f"<div style='text-align: left; padding: 5px; border-radius: 5px; background-color: #e1f5fe; color: black;'><b>{chat['sender']}:</b> {chat['message']}</div>", 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align: right; padding: 5px; border-radius: 5px; background-color: #ffe0b2; color: black;'><b>{chat['sender']}:</b> {chat['message']}</div>", 
                    unsafe_allow_html=True
                )

    # Clear All button
    if st.button("Clear All"):
        st.session_state.chat_history.clear()
        st.markdown(
            f"""
            <div style="font-size: 23px; color: black; background-color: rgba(7, 228, 36, 0.88); 
                        padding: 20px; border-radius: 8px;
                        margin-top: 20px; 
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                Chat History Cleared
            </div>
            """,
            unsafe_allow_html=True
        )
        st.rerun()
def show_account_page():
    add_bg_image("https://www.pixelstalk.net/wp-content/uploads/2016/10/Free-blue-green-wallpaper-HD.jpg")
    col1, col2 = st.columns(2)
    with col1:
        st.image(image_path1, width=60)
    with col2:
        st.markdown(
            """
            <h1 style="font-size: 50px; font-weight: 900; color: #ffff; margin-bottom: 20px; margin-left: -290px; margin-top: -20px">Your Profile</h1>
            """,
            unsafe_allow_html=True
        )
    # Custom styling for user details
    st.markdown(
            """
            <style>
                .account-title {
                    font-size: 24px; /* Title font size */
                    color: #007bff; /* Title color */
                    margin-bottom: 20px; /* Space below the title */
                }
                .account-details {
                    font-size: 18px; /* Details font size */
                    color: #333; /* Details text color */
                    margin-bottom: 10px; /* Space below each detail */
                    background-color: rgba(255, 255, 255, 0.8); /* Slightly transparent background */
                    padding: 10px; /* Padding around the details */
                    border-radius: 8px; /* Rounded corners */
                    border: 1px solid #007bff; /* Border color */
            }
        </style>
        """,
        unsafe_allow_html=True
    )
# Check if user details are in session state
    if "user_details" in st.session_state and st.session_state["user_details"] is not None:
        user_details = st.session_state["user_details"]
        # Display user details with inline CSS
        st.markdown(
            """
            <style>
            .user-details {
                background-color: rgba(255, 255, 255, 0.8);
                color: blue;
                padding: 20px 10px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease, background 0.3s ease;
            }
            .user-details:hover {
                transform: scale(1.05); /* Slightly enlarge on hover */
            }
            .user-details strong {
                color: black;
                font-size: 30px; /* Golden color for labels */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Display user details in the styled box
        st.markdown(
            f"""
            <div class='user-details'>
                <strong>Username:</strong>  {user_details['username']}<br>
            </div><br>
            <div class='user-details'>
                <strong>Name:</strong> {user_details['name']}<br>
            </div><br>
            <div class='user-details'>
                <strong>Email:</strong> {user_details['email']}<br>
            </div><br>
            <div class='user-details'>
                <strong>Phone:</strong> {user_details['phone']}<br>
            </div>
            <br>
            """,
            unsafe_allow_html=True
        )

        # Hidden Streamlit button for logout logic
        if st.button("Log out", key="logout-button", help="Log out and clear session state"):
            st.session_state.clear()
            st.success("You have logged out successfully.")
            st.session_state["show_login"] = True
            st.rerun()
            
    else:
        st.markdown(
            """
            <div style="font-size: 18px; color: #fff; background-color: rgba(255, 0, 0, 0.7); 
                        padding: 10px; border-radius: 8px; text-align: center; 
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);">
                User not logged in.
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Login"):
            st.session_state["show_login"] = True  # Set to show the login page
            st.markdown('<div class="success-message">Redirecting to login page...</div>', unsafe_allow_html=True)
            st.rerun()
# Display the appropriate page based on the selected option
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None  # Initialize username
# Initialize session state for sidebar state and selected card
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = True
if "selected_card" not in st.session_state:
    st.session_state.selected_card = None

def sidebar():
    add_sidebar_image("https://img.freepik.com/free-vector/background-banner-colorful-gradient_677411-3588.jpg?t=st=1728405915~exp=1728409515~hmac=25391513b16dfb58596f5207d16dc1e5f38f218d978d62e23aab6f9a243d9b74&w=360")
    st.session_state.sidebar_state = not st.session_state.sidebar_state

    def sidebar_toggle_button():
        icon = "⬅️" if st.session_state.sidebar_state else "➡️"  # Icon change
        st.markdown(f"""
            <style>
                .toggle-btn {{
                    position: fixed;
                    top: 15px;
                    left: 15px;
                    background-color: #33006F;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    font-size: 18px;
                    border-radius: 5px;
                    cursor: pointer;
                    z-index: 1000;
                }}
                .toggle-btn:hover {{
                    background-color: #33006F;
                }}
            </style>
            <button class="toggle-btn" onclick="toggleSidebar()">{icon}</button>

            <script>
                function toggleSidebar() {{
                    var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                    if (sidebar.style.display === "none") {{
                        sidebar.style.display = "block";
                        window.parent.document.querySelector('.toggle-btn').innerText = "⬅️";
                    }} else {{
                        sidebar.style.display = "none";
                        window.parent.document.querySelector('.toggle-btn').innerText = "➡️";
                    }}
                }}
            </script>
        """, unsafe_allow_html=True)

    # Call the function to display the toggle button
    sidebar_toggle_button()

    st.sidebar.markdown(
        f"""
        <div style="text-align: center; margin-top: -20px;">
           <h4 style="color: black !important; font-size: 30px; font-weight: 900; margin-top: 10px">WordVibe</h4>
            <img src="data:image/png;base64,{logo_image}" style="width: 75%; max-width: 150px; margin-top: -25px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        """
        <style>
        p {
            font-size: 20px !important;
            font-weight: 900 !important;
        }
        .sidebar-radio {
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar content
    st.sidebar.markdown('<div class="sidebar-radio">', unsafe_allow_html=True)

    # Radio button selection
    selected_page = st.sidebar.radio("Menu", 
                                ["🏠 Home", 
                                 "👤 Account", 
                                 "❓ Help",
                                 "📞Contact us"], 
                                key="sidebar_navigation")
    st.sidebar.markdown('<div class="sidebar-radio">', unsafe_allow_html=True)

    if selected_page != "🏠 Home":
        st.session_state.selected_card = None
    
    # Show remaining cards in the sidebar if a card is selected and "Home" is selected
    if selected_page == "🏠 Home" and st.session_state.selected_card is not None:
        st.sidebar.markdown(
            '<h3 style="font-size: 20px; font-weight: bold; color: #33006F; margin-top: -30px;">Other Cards</h3>', 
            unsafe_allow_html=True
        )
        if st.session_state.selected_card != "Text to Speech":
            if st.sidebar.button("Text to Speech"):
                st.session_state.selected_card = "Text to Speech"
                st.rerun()
        if st.session_state.selected_card != "Speech to Text":
            if st.sidebar.button("Speech to Text"):
                st.session_state.selected_card = "Speech to Text"
                st.rerun()
        if st.session_state.selected_card != "Text to Text":
            if st.sidebar.button("Text to Text"):
                st.session_state.selected_card = "Text to Text"
                st.rerun()
        if st.session_state.selected_card != "Image to Speech":
            if st.sidebar.button("Image to Speech"):
                st.session_state.selected_card = "Image to Speech"
                st.rerun()
    st.sidebar.markdown(
        """
        <h3 style='color: #000; font-size: 20px; margin-top: -20px;'>Guided by Mr.Abdul Aziz Md</h3>
        """,
        unsafe_allow_html=True
    )
    if selected_page == "🏠 Home":
        show_home_page()  # Define this function
    elif selected_page == "👤 Account":
        show_account_page()  # Define this function
    elif selected_page == "❓ Help":
        show_help_page()
    elif selected_page == "📞Contact us":
        # Function to add a custom background with a vibrant blue theme
        def background():
            page_bg_style = '''
            <style>
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(to right, #007BFF, #90EE90);
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                
            }
            /* Sidebar width customization */
            
            [data-testid="stHeader"], [data-testid="stToolbar"] {
                background: rgba(0,0,0,0); /* Hides header */
            }
            h1 {
                color: #FFFFFF; /* White color for the heading */
                font-size: 40px;
            }
            h2 h4, h5 {
                color: #FFDD00; /* Distinct gold color for subheadings */
            }
            p {
                font-size: 18px !important;
            }
            .highlight-email {
                font-size: 20px;
                font-weight: bold;
                color: #FF5733; /* Bright orange for the email */
                background-color: #FFF3CD; /* Light yellow background */
                padding: 5px 10px;
                border-radius: 5px;
                display: inline-block;
            }
            .stTable {
                background-color: white; /* Light background for the table to improve readability */
            }
            </style>
            '''
            st.markdown(page_bg_style, unsafe_allow_html=True)

        background()
        
        # Contact Us Section with white heading color
        st.title("Contact Us")
        
        st.write("If you have any questions or need support, please feel free to reach out:")

        # Highlighted email
        st.markdown('<p class="highlight-email">ravinaryanab25@gmail.com</p>', unsafe_allow_html=True)
        
        st.write("---")
        # Contact details in a table
        data = [
            ["Leader", "BRAHMA RAVI NARAYANA", "6300947536","ravinaryanab25@gmail.com"],
            ["Team #1", "CHOPPARLA SAITEJA", "6300316947","saitejachopparla@gmail.com"],
            ["Team #2", "PUTHI SATHISH","6281529344","satishputhi14@gmail.com"],
            ["Team #3", "MIRTHIPATHI SYAMSUNDAR", "8374833713","syamsundarmirthipathi123@gmail.com"]
        ]
        df = pd.DataFrame(data, columns=["Position","Name", "Phone Number","E-Mail"])
        st.table(df)  # Define this function

# Entry point of the Streamlit app
if __name__ == "__main__":
    # Initialize database (define init_db function)
    init_db()
    # Session state management
    if "show_login" not in st.session_state:
        st.session_state["show_login"] = True
    if "show_signup" not in st.session_state:
        st.session_state["show_signup"] = False
    if "show_home_page" not in st.session_state:
        st.session_state["show_home_page"] = True  # Set to True for home page
    if "show_recovery" not in st.session_state:
        st.session_state["show_recovery"] = False
    # Display the appropriate page
    if st.session_state["show_login"]:
        show_login_page()  # Define this function for the login page
    elif st.session_state["show_signup"]:
        show_signup_page()  # Define this function for the signup page
    elif st.session_state.get("show_recovery"):
        show_password_recovery_page()  # Define this function for password recovery
    else:
        sidebar()
