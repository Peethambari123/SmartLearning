import os
import time
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build

# Configure Google Gemini API key
API_KEY = "AIzaSyAPS9hfiQ-IlF3HzybSt-SGR_ZP4S3ONgU"
genai.configure(api_key=API_KEY)

# Configure YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyDjjpWFszcgYsc4qc_4cFh5n62kRBzUVqo"
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# [Previous functions remain exactly the same...]

# Custom CSS for warm red-brown (#8B4513) color scheme
st.markdown(
    """
    <style>
    .stApp {
        background: #8B4513;  /* Warm saddle brown background */
        color: #FFF8DC;       /* Cream text for contrast */
        font-family: 'Georgia', serif;
    }
    .stButton>button {
        background-color: #A0522D !important;  /* Sienna brown */
        color: #FFF8DC !important;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #8B4513 !important;  /* Darker brown */
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 248, 220, 0.9) !important;  /* Cream */
        color: #333333 !important;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #A0522D;
    }
    .stRadio>div {
        background-color: rgba(255, 248, 220, 0.8) !important;  /* Semi-transparent cream */
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #A0522D;
    }
    .stHeader {
        color: #FFD700 !important;  /* Gold headers */
        text-shadow: 1px 1px 2px #000000;
    }
    .stMarkdown {
        color: #FFF8DC;  /* Cream text */
    }
    .timer {
        color: #FFD700 !important;  /* Gold timer */
        font-weight: bold;
        font-size: 1.3rem;
        background-color: rgba(139, 69, 19, 0.7);
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
    }
    .quiz-card {
        background-color: rgba(255, 248, 220, 0.9) !important;  /* Cream cards */
        color: #333333 !important;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        border: 1px solid #A0522D;
    }
    .sidebar .sidebar-content {
        background-color: #A0522D !important;  /* Sienna sidebar */
        color: #FFF8DC !important;
    }
    .stChatMessage {
        background-color: rgba(255, 248, 220, 0.9) !important;
        color: #333333 !important;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #A0522D;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# [Rest of your existing code remains exactly the same...]

# Only update the results display section in Quiz Challenge mode:
if st.session_state.quiz_submitted:
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

    # Results card with warm brown accent
    st.markdown(
        f"""
        <div style="background-color: #A0522D; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: #FFF8DC;">
            <h2 style="color: #FFD700;">Quiz Results</h2>
            <h3>Your Score: {score}/{len(questions)} ({(score/len(questions))*100:.1f}%)</h3>
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
                <span style="color: {'#228B22' if fb['is_correct'] else '#B22222'}">
                {'✅' if fb['is_correct'] else '❌'} Your Answer: {fb['user_answer']}</span><br>
                <b>Correct Answer:</b> {fb['correct_answer']}
            </div>
            """,
            unsafe_allow_html=True
        )
