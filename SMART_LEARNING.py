import os
import time
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build

# Configure Google Gemini API key (should use environment variables in production)
API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your actual key
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your actual key
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to read the PDF file
def read_pdf(file_path):
    """Reads the text from a PDF file."""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

# Function to query the Gemini LLM with preloaded context
def query_with_cag(context: str, query: str) -> str:
    """Query the Gemini LLM with preloaded context."""
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to search YouTube and generate links
def search_youtube(query: str, max_results: int = 5):
    """Search YouTube for videos related to the query."""
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    videos = []
    for item in response["items"]:
        video_id = item["id"]["videoId"]
        video_title = item["snippet"]["title"]
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({"title": video_title, "link": video_link})
    return videos

# Function to generate quiz questions from PDF text
def generate_quiz_from_pdf(pdf_text: str, num_questions: int = 5):
    """Generate quiz questions from the PDF text."""
    prompt = f"Generate {num_questions} multiple-choice questions based on:\n\n{pdf_text}\n\nEach question should have 4 options (a), b), c), d)) and a correct answer labeled as 'Correct Answer:'."
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

# Initialize session state
if "chat" not in st.session_state:
    st.session_state.chat = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

# Custom CSS for light purple theme
st.markdown(
    """
    <style>
    .stApp {
        background: #F3E5FF;  /* Very light purple background */
        color: #4B0082;       /* Indigo text */
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #9370DB !important;  /* Medium purple */
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #8A2BE2 !important;  /* Blue violet */
        transform: scale(1.02);
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #BA55D3;
        border-radius: 8px;
        padding: 10px;
    }
    .stRadio>div {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #BA55D3;
    }
    .stHeader {
        color: #6A0DAD !important;  /* Dark purple headers */
    }
    .timer {
        color: #8A2BE2;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .quiz-card {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #BA55D3;
    }
    .sidebar .sidebar-content {
        background-color: #9370DB !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App Interface
st.title("🤖 Smart Learning Assistant")
st.write("Chat with AI, query PDFs, search YouTube, or take quizzes!")

# Sidebar navigation
app_mode = st.sidebar.radio(
    "Choose Mode", 
    ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"],
    key="nav"
)

# [Rest of your mode implementations remain the same...]
# Make sure to properly indent all the mode implementations (Chat, PDF Query, YouTube, Quiz)

# For the quiz results section, update to:
if st.session_state.get("quiz_submitted", False):
    score = 0
    feedback = []
    for i, q in enumerate(questions, 1):
        user_answer = st.session_state.user_answers.get(i)
        correct_answer = q["correct"]
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        feedback.append({
            "question": q["text"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    st.markdown(
        f"""
        <div style="background-color: #9370DB; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white;">
            <h2>Quiz Results</h2>
            <h3>Score: {score}/{len(questions)} ({(score/len(questions))*100:.1f}%)</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("### Detailed Feedback")
    for fb in feedback:
        st.markdown(
            f"""
            <div class="quiz-card">
                <b>Question:</b> {fb['question']}<br><br>
                <span style="color: {'#2E8B57' if fb['is_correct'] else '#B22222'}">
                {'✅' if fb['is_correct'] else '❌'} Your Answer: {fb['user_answer']}</span><br>
                <b>Correct Answer:</b> {fb['correct_answer']}
            </div>
            """,
            unsafe_allow_html=True
        )
