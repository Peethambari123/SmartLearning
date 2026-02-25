import os
import time
import streamlit as st
from google import genai
from PyPDF2 import PdfReader
from googleapiclient.discovery import build

# ================= GEMINI CONFIG =================
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
client = genai.Client()

# ================= YOUTUBE CONFIG =================
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# ================= PDF READER =================
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

# ================= GEMINI QUERY =================
def query_with_cag(context: str, query: str) -> str:
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

# ================= QUIZ GENERATOR =================
def generate_quiz_from_pdf(pdf_text: str, num_questions: int = 5):
    prompt = f"Generate {num_questions} multiple-choice questions based on the following text:\n\n{pdf_text}\n\nEach question should have 4 options (a), b), c), d)) and a correct answer labeled as 'Correct Answer:'."
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

# ================= YOUTUBE SEARCH =================
def search_youtube(query: str, max_results: int = 5):
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

# ================= CHAT INIT =================
if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-1.5-flash"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

# ================= UI =================
st.title("🤖 Chatbot & PDF Query App")
st.write("Welcome! You can chat with the AI, upload a PDF to query its content, search for YouTube videos, or take a quiz.")

st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose Mode", ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"])

# ================= CHAT MODE =================
if app_mode == "Chat with AI":
    st.header("Chat with AI")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Say something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        response = st.session_state.chat.send_message(prompt)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response.text
        })

        with st.chat_message("assistant"):
            st.markdown(response.text)

# ================= PDF QUERY =================
elif app_mode == "Query a PDF":
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf("temp.pdf")
        st.session_state.pdf_text = pdf_text

    if st.session_state.pdf_text:
        query = st.text_input("Ask a question about the PDF:")
        if query:
            answer = query_with_cag(st.session_state.pdf_text, query)
            st.markdown(answer)

# ================= YOUTUBE =================
elif app_mode == "Search YouTube":
    youtube_query = st.text_input("Enter a search term:")
    if youtube_query:
        videos = search_youtube(youtube_query)
        for video in videos:
            st.markdown(f"[{video['title']}]({video['link']})")

# ================= QUIZ =================
elif app_mode == "Quiz Challenge":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        with open("quiz.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf("quiz.pdf")
        quiz = generate_quiz_from_pdf(pdf_text)
        st.text_area("Quiz", quiz, height=300)
