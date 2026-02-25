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
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def query_with_cag(context: str, query: str) -> str:
    prompt = f"Context:\n{context}\n\nQuery: {query}\nAnswer:"
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text.strip()

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

def generate_quiz_from_pdf(pdf_text: str, num_questions: int = 5):
    prompt = f"Generate {num_questions} multiple-choice questions based on the following text:\n\n{pdf_text}"
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text

if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-1.5-flash"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.pdf_text = None

st.title("🤖 Chatbot & PDF Query App")
st.write("Welcome! You can chat with the AI, upload a PDF to query its content, search for YouTube videos, or take a quiz.")

st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose Mode", ["Chat with AI", "Query a PDF", "Search YouTube", "Quiz Challenge"])
if app_mode == "Chat with AI":
    st.header("Chat with AI")
    st.write("Ask me anything!")

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

elif app_mode == "Query a PDF":
    st.header("Query a PDF")
    st.write("Upload a PDF and ask questions about its content.")

    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    if uploaded_file is not None:
        temp_file_path = "temp.pdf"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf(temp_file_path)
        st.session_state.pdf_text = pdf_text
        st.text_area("PDF Content Preview", value=pdf_text[:500], height=100)

    if st.session_state.pdf_text:
        query = st.text_input("Ask a question about the PDF:")
        if query:
            with st.spinner("Processing your query..."):
                answer = query_with_cag(st.session_state.pdf_text, query)
                st.markdown(f"**Answer:** {answer}")
                elif app_mode == "Search YouTube":
    st.header("Search YouTube")
    st.write("Search for YouTube videos related to your query.")

    youtube_query = st.text_input("Enter a search term:")
    if youtube_query:
        with st.spinner("Searching YouTube..."):
            videos = search_youtube(youtube_query)
            st.write("### Results:")
            for video in videos:
                st.markdown(f"[{video['title']}]({video['link']})")

elif app_mode == "Quiz Challenge":
    st.header("Quiz Challenge")
    st.write("Upload a PDF and take a timed quiz based on its content.")

    if "quiz_start_time" not in st.session_state:
        st.session_state.quiz_start_time = None
    if "time_remaining" not in st.session_state:
        st.session_state.time_remaining = 300
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    uploaded_file = st.file_uploader("Please upload a PDF file", type="pdf", key="quiz_pdf_uploader")
    if uploaded_file is not None:
        temp_file_path = "quiz.pdf"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        pdf_text = read_pdf(temp_file_path)
        st.session_state.pdf_text = pdf_text
        st.text_area("PDF Content Preview", value=pdf_text[:500], height=100)

        st.write("### Generating Quiz Questions...")
        quiz_questions = generate_quiz_from_pdf(pdf_text)
                lines = quiz_questions.split("\n")
        questions = []
        current_question = {}
        options = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and "." in line[:3]:
                if current_question and options:
                    current_question["options"] = options
                    questions.append(current_question)
                question_text = line.split(".", 1)[1].strip()
                current_question = {"text": question_text}
                options = []
            elif any(line.startswith(opt) for opt in ["a)", "b)", "c)", "d)"]):
                options.append(line)
            elif line.lower().startswith("correct answer:"):
                correct_answer = line.split(":", 1)[1].strip()
                current_question["correct"] = correct_answer

        if current_question and options:
            current_question["options"] = options
            questions.append(current_question)

        st.write("### Quiz Questions")
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Question {i}: {q['text']}**")
            user_answer = st.radio(
                f"Select your answer for Question {i}",
                q["options"],
                key=f"quiz_q{i}"
            )
            st.session_state.user_answers[i] = user_answer
