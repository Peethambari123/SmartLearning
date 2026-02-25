import os
import time
import streamlit as st
from google import genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build

os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
client = genai.Client()

YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def gemini_generate(prompt):
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

def search_youtube(query, max_results=5):
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

st.title("🤖 Chatbot & PDF Query App")
st.sidebar.title("Navigation")

app_mode = st.sidebar.radio(
    "Choose Mode",
    ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"]
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if app_mode == "Chat with AI":
    st.header("Chat with AI")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Say something..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = gemini_generate(prompt)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        with st.chat_message("assistant"):
            st.markdown(response)

elif app_mode == "Query a PDF":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        pdf_text = read_pdf("temp.pdf")
        query = st.text_input("Ask a question about the PDF:")
        if query:
            answer = gemini_generate(f"{pdf_text}\n\nQuestion: {query}")
            st.markdown(answer)

elif app_mode == "Search YouTube":
    youtube_query = st.text_input("Enter topic:")
    if youtube_query:
        videos = search_youtube(youtube_query)
        for video in videos:
            st.markdown(f"[{video['title']}]({video['link']})")

elif app_mode == "Quiz Challenge":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        with open("quiz.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        pdf_text = read_pdf("quiz.pdf")
        quiz = gemini_generate(
            f"Generate 5 MCQs from this text:\n{pdf_text}"
        )
        st.text_area("Quiz", quiz, height=300)
