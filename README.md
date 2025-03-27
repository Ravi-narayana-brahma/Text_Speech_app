# **🗣️ WordVibe - AI-powered Speech & Text Processing App**  

## **📌 About the Project**  
**WordVibe** is an AI-driven application that provides **Text-to-Speech (TTS), Speech-to-Text (STT), Text-to-Text (Translation/Summarization), and Image-to-Text-to-Speech** functionalities. It enhances accessibility and language processing, making it ideal for various speech and text-based applications.  

## **🚀 Features**  
✅ **Text-to-Speech (TTS):** Convert text into speech using **gTTS & pyttsx3**  
✅ **Speech-to-Text (STT):** Transcribe spoken words into text using **SpeechRecognition**  
✅ **Text-to-Text Translation:** Translate text between multiple languages using **Google Translate API**  
✅ **Image-to-Text-to-Speech:** Extract text from images with **EasyOCR** and convert it into speech  
✅ **Real-Time Microphone Input:** Capture voice input using **Streamlit Mic Recorder**  
✅ **Database Integration:** Uses **SQLite3** for user authentication & data storage  
✅ **Live Audio Processing:** Perform real-time speech recognition via **Streamlit WebRTC**  
✅ **Secure Login System:** Implements **bcrypt hashing** for authentication security  
✅ **Base64 Encoding:** Securely store and process data  

## **🛠️ Tech Stack**  
- **Frontend & UI:** Streamlit  
- **Backend & Processing:** Python  
- **Audio Processing:** `pydub`, `pyaudio`, `ffmpeg`  
- **Speech Recognition:** `SpeechRecognition`  
- **Text-to-Speech:** `gTTS`, `pyttsx3`  
- **Image Processing:** `PIL`, `EasyOCR`, `torch`, `torchvision`  
- **Database:** SQLite3  

---

## **📥 Installation & Setup**  

### **1️⃣ Clone the Repository**  
```bash
git clone https://github.com/Ravi-narayana-brahma/Text_Speech_app.git
cd Text_Speech_app
```  

### **2️⃣ Create a Virtual Environment (Recommended)**  
```bash
python -m venv venv
source venv/bin/activate  # For Mac/Linux
venv\Scripts\activate  # For Windows
```  

### **3️⃣ Install Dependencies**  
Run the following command to install all required libraries manually:  
```bash
pip install streamlit pandas numpy sqlite3 base64 smtplib pyaudio pydub SpeechRecognition gTTS pyttsx3 streamlit-mic-recorder streamlit-webrtc ffmpeg torch==2.6.0 torchvision==0.21.0 easyocr pillow av bcrypt googletrans==4.0.0-rc1
```  

### **4️⃣ Install FFmpeg (Manual Installation Required)**  
FFmpeg is needed for audio processing. Follow these steps:  

🔹 **Windows:**  
1. Download FFmpeg from [official website](https://ffmpeg.org/download.html)  
2. Extract the files and add the **bin** folder path to the system's **Environment Variables**  
3. Verify installation using:  
   ```bash
   ffmpeg -version
   ```  

🔹 **Mac/Linux:**  
```bash
sudo apt update && sudo apt install ffmpeg
ffmpeg -version
```  

### **5️⃣ Run the Application**  
```bash
streamlit run app.py
```  

---

## **🎯 How to Use**  

### **🔹 Text-to-Speech (TTS):**  
- Enter text and click **Convert** to generate speech.  
- Download or listen to the generated speech file.  

### **🔹 Speech-to-Text (STT):**  
- Upload an audio file or speak directly into the microphone.  
- Click **Transcribe** to convert speech into text.  

### **🔹 Text-to-Text:**  
- Paste text to be translated, summarized, or processed.  
- Select options like **Summarize** or **Translate**.  

### **🔹 Image-to-Text-to-Speech:**  
- Upload an image containing text.  
- The app extracts the text and reads it aloud.  

---

## **🔮 Future Enhancements**  
🚀 Add real-time speech recognition  
🚀 Improve speech synthesis using deep learning models  
🚀 Implement AI-powered text summarization & translation  
🚀 Support additional languages and accents  

---

## **🤝 Contributing**  
Contributions are welcome! Feel free to fork this repository and submit a pull request.  

---

## **🔗 Contact & Links**  
🔗 GitHub: [Ravi Narayana Brahma](https://github.com/Ravi-narayana-brahma)  

---
